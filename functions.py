import globus_compute_sdk
from dotenv import load_dotenv
import os
import argparse

load_dotenv(dotenv_path="./fusion.env")

def fusion_wrapper(run_directory, config_path="ionorb_stl2d_boris.config", outfile="out.hits.els.txt"):
    import subprocess, os, time, shutil

    start = time.time()
    os.chdir(run_directory)
    command = f"/eagle/IRIBeta/bin/ionorb_stl_boris2d {config_path}"
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

def make_plots(run_directory, hits_file="out.hits.els.txt"):
    import sys
    import os
    import glob
    import shutil

    sys.path.append("/eagle/IRIBeta/bin")
    from fusion_plots import make_all_plots

    os.chdir(run_directory)
    try:
        make_all_plots(hits_file)
    except Exception as e:
        return "Failure"

    plots = glob.glob("*.png")
    for plot in plots:
        try:
            shutil.copy(plot,os.path.join(run_directory,"outputs",plot))
        except:
            os.makedirs(os.path.join(run_directory,"outputs"))
            shutil.copyfile(plot,os.path.join(run_directory,"outputs",plot))
    return "Success",plots

def register_function(function):
    
    if function == fusion_wrapper:
        envvarname = "FUSION_FUNCTION_ID"
    elif function == make_plots:
        envvarname = "PLOT_FUNCTION_ID"
    else:
        return "Unknown function"
    gc = globus_compute_sdk.Client()
    fusion_func = gc.register_function(function)
    with open("fusion.env", "a") as f:
        f.write(f"{envvarname}={fusion_func}\n")
    return f"{envvarname}={fusion_func}"

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=False, action='store_true', help=f'Test Function')
    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    if args.test:
        print("Testing functions")
        functions = [fusion_wrapper, make_plots]
        for function in functions:
            print(function)
            gce = globus_compute_sdk.Executor(endpoint_id=os.getenv("GLOBUS_COMPUTE_ENDPOINT"))
            
            
            params= ["/eagle/datascience/csimpson/fusion/dummy_data/"]
            future = gce.submit(function,*params)
            try:
                print(future.result())
            except Exception as e:
                print(e)
    else:
        print("Registering functions")
        functions = [fusion_wrapper,make_plots]
        for function in functions:
            register_function(function)
