import globus_compute_sdk
from dotenv import load_dotenv
import os
import argparse
from start_fusion_flow import machine_settings

load_dotenv(dotenv_path="./fusion.env")

def ionorb_wrapper(run_directory, config_path="ionorb_stl2d_boris.config", outfile="out.hits.els.txt"):
    import subprocess, os, time, shutil

    start = time.time()
    os.chdir(run_directory)
    command = f"ionorb_stl_boris2d {config_path}"
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

def hello_world():
    import os
    return f"Hello CUDA device {os.getenv('CUDA_VISIBLE_DEVICES')}, hello OMP {os.getenv('OMP_NUM_THREADS')}"

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

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', default=False, action='store_true', help=f'Test Function')
    parser.add_argument('--machine', default='polaris', help=f'Target machine for flow', choices=machine_settings.keys())
    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    if args.test:
        machine = args.machine
        settings = machine_settings[machine]
        if machine == "polaris":
            settings['scratch_path'] = "/eagle"+settings['scratch_path']

        print(f"Testing functions on {machine}")
        functions = [hello_world, ionorb_wrapper, heatmapping]
        for function in functions:
            print(function) 
            gce = globus_compute_sdk.Executor(endpoint_id=settings["compute_endpoint"])

            params = []
            if function == ionorb_wrapper:
                params= [os.path.join(settings["scratch_path"],"test_runs/test")]
            elif function == heatmapping:
                params= [settings["bin_path"], 
                         os.path.join(settings["scratch_path"],"test_runs/test")]
            
            future = gce.submit(function,*params)
            print(future.result())
            
    else:
        print("Registering functions")
        functions = [ionorb_wrapper,make_plots,heatmapping]
        for function in functions:
            register_function(function)
