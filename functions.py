import globus_compute_sdk
from dotenv import load_dotenv
import os
import argparse

load_dotenv(dotenv_path="./fusion.env")

def ionorb_wrapper(app_path, run_directory, config_path="ionorb_stl2d_boris.config", outfile="out.hits.els.txt"):
    import subprocess, os, time, shutil

    start = time.time()
    os.chdir(run_directory)
    command = f"{app_path} {config_path}"
    res = subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    end = time.time()
    runtime = end - start

    if res.returncode != 0:
        raise Exception(f"Application failed with non-zero return code: {res.returncode} stdout='{res.stdout.decode('utf-8')}' stderr='{res.stderr.decode('utf-8')}' runtime={runtime}")
    else:
        try:
            shutil.copyfile(outfile,os.path.join(run_directory,"outputs",outfile))
        except:
            os.makedirs(os.path.join(run_directory,"outputs"))
            shutil.copyfile(outfile,os.path.join(run_directory,"outputs",outfile))
        return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8"), runtime

def heatmapping(python_path, run_directory, config_path="./ionorb_stl2d_boris.config"):

    import sys
    import os
    import glob
    import shutil

    sys.path.append(python_path)
    from fusion_plots import plot_2Dhist

    os.chdir(run_directory)
    try:
        peak,Phi,z = plot_2Dhist(config_filename=config_path)
    except Exception as e:
        return f"Failure {e}"

    plots = glob.glob("*.png")
    for plot in plots:
        try:
            shutil.copy(plot,os.path.join(run_directory,"outputs",plot))
        except:
            os.makedirs(os.path.join(run_directory,"outputs"))
            shutil.copyfile(plot,os.path.join(run_directory,"outputs",plot))
    return "Success",peak,Phi,z,plots

def make_plots(python_path, run_directory, hits_file="out.hits.els.txt"):
    import sys
    import os
    import glob
    import shutil

    sys.path.append(python_path)
    from fusion_plots import make_all_plots

    os.chdir(run_directory)
    try:
        make_all_plots(hits_file)
    except Exception as e:
        return f"Failure {e}"

    plots = glob.glob("*.png")
    for plot in plots:
        try:
            shutil.copy(plot,os.path.join(run_directory,"outputs",plot))
        except:
            os.makedirs(os.path.join(run_directory,"outputs"))
            shutil.copyfile(plot,os.path.join(run_directory,"outputs",plot))
    return "Success",plots

def register_function(function):
    
    if function == ionorb_wrapper:
        envvarname = "IONORB_FUNCTION_ID"
    elif function == make_plots:
        envvarname = "PLOT_FUNCTION_ID"
    elif function == heatmapping:
        envvarname = "HEATMAP_FUNCTION_ID"
    else:
        return "Unknown function"
    gc = globus_compute_sdk.Client()
    fusion_func = gc.register_function(function)
    with open("fusion.env", "a") as f:
        f.write(f"{envvarname}={fusion_func}\n")
    return f"{envvarname}={fusion_func}"

# def untar(tarfile):
#     import subprocess

#     command = f"tar xvf {tarfile}"
#     res = subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     if res.returncode != 0:
#         raise Exception(f"Untar failed: {res.returncode} stdout='{res.stdout.decode('utf-8')}' stderr='{res.stderr.decode('utf-8')}'")
#     else:
#         return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=False, action='store_true', help=f'Test Function')
    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    if args.test:
        print("Testing functions")
        functions = [ionorb_wrapper, make_plots, heatmapping]
        for function in functions:
            print(function)

            # gce = globus_compute_sdk.Executor(endpoint_id=os.getenv("GLOBUS_COMPUTE_PERLMUTTER_ENDPOINT"))
            
            # if function == ionorb_wrapper:
            #     params= ["/global/homes/c/csimpson/ionorbgpu/v2/boris2d_stl/bin/ionorb_stl_boris2d", 
            #             "/global/homes/c/csimpson/ionorb_test"]
            # else:
            #     params= ["/global/homes/c/csimpson/fusion_compute/analysis",
            #              "/global/homes/c/csimpson/ionorb_test",]
                
            gce = globus_compute_sdk.Executor(endpoint_id=os.getenv("GLOBUS_COMPUTE_POLARIS_ENDPOINT"))
            
            if function == ionorb_wrapper:
                params= ["/eagle/IRIBeta/fusion/bin/ionorb_stl_boris2d", 
                        "/eagle/datascience/csimpson/fusion/dummy_data"]
            else:
                params= ["/eagle/IRIBeta/fusion/bin",
                         "/eagle/datascience/csimpson/fusion/dummy_data",]


            future = gce.submit(function,*params)
            try:
                print(future.result())
            except Exception as e:
                print(e)
    else:
        print("Registering functions")
        functions = [ionorb_wrapper,make_plots,heatmapping]
        for function in functions:
            register_function(function)
