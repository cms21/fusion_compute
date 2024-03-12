import globus_compute_sdk
from dotenv import load_dotenv
from fusion_compute import ENV_PATH
import os
import argparse
from fusion_compute.machine_settings import machine_settings

load_dotenv(dotenv_path=ENV_PATH)

def ionorb_wrapper(run_directory, bin_path, config_path="ionorb_stl2d_boris.config", outfile="out.hits.els.txt"):
    import subprocess, os, time, shutil, glob

    start = time.time()
    os.chdir(run_directory)

    if len(glob.glob("*.stl")+glob.glob("*.STL")) == 0:
        stl_files = glob.glob(os.path.join(bin_path,"*.stl"))+glob.glob(os.path.join(bin_path,"*.STL"))
        for stl_file in stl_files:
            stl_file_name = stl_file.split("/")[-1]
            os.symlink(stl_file,os.path.join(run_directory,stl_file_name))

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


def make_input_scripts(run_directory, shot=164869, stime=3005, efitnum="EFIT01", profdata=1, beam_num=1, energykev="FULL", nparts=1000):
    import os, time, subprocess, glob

    start = time.time()

    if not os.path.exists(run_directory):
        os.makedirs(run_directory)
    os.chdir(run_directory)

    # Create B field file
    command = f"ionorb_createB {shot} {stime} {efitnum}"
    res = subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or len(glob.glob("B_*.txt")) == 0:
        end = time.time()
        runtime = end - start
        raise Exception(f"createB failed: {res.returncode} stdout='{res.stdout.decode('utf-8')}' stderr='{res.stderr.decode('utf-8')}' runtime={runtime} command={command}")

    # Create birth file
    command = f"ionorb_create_birth {shot} {stime} {efitnum} {profdata} {beam_num} {energykev} {nparts}"
    res = subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or len(glob.glob("birth*.dat")) == 0:
        end = time.time()
        runtime = end - start
        raise Exception(f"create_birth failed: {res.returncode} stdout='{res.stdout.decode('utf-8')}' stderr='{res.stderr.decode('utf-8')}' runtime={runtime} command={command}")
    
    # Create config file
    command = f"/home/simpsonc/ionorbgpu/v2/tools/ionorb_generate_config"
    res = subprocess.run(command.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or len(glob.glob("*.config")) == 0: #or len(glob.glob("*.stl")) == 0:
        end = time.time()
        runtime = end - start
        raise Exception(f"config failed: {res.returncode} {len(glob.glob('*.config'))} {len(glob.glob('*.stl'))} stdout='{res.stdout.decode('utf-8')}' stderr='{res.stderr.decode('utf-8')}' runtime={runtime} command={command}")

    end = time.time()
    runtime = end - start
    return f"Input files created, runtime={runtime}"
# arange(200,5000,100)
# shot=163303
def register_function(function):
    
    if function == ionorb_wrapper:
        envvarname = "IONORB_FUNCTION_ID"
    elif function == make_plots:
        envvarname = "PLOT_FUNCTION_ID"
    elif function == heatmapping:
        envvarname = "HEATMAP_FUNCTION_ID"
    elif function == make_input_scripts:
        envvarname = "INPUTS_FUNCTION_ID"
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
    parser.add_argument('--machine', default='polaris', help=f'Target machine for flow', choices=machine_settings().keys())
    parser.add_argument('--function', default='all', help=f'Function to register', choices=[ionorb_wrapper.__name__,
                                                                                            make_plots.__name__,
                                                                                            heatmapping.__name__,
                                                                                            make_input_scripts.__name__])
    
    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()

    if args.test:
        machine = args.machine
        settings = machine_settings()[machine]
        if machine == "polaris":
            settings['scratch_path'] = "/eagle"+settings['scratch_path']

        print(f"Testing functions on {machine}")

        if machine == "omega":
            # These functions only run at D3D
            functions = [hello_world, make_input_scripts]
        else:
            # These functions are setup on ASCR machines
            functions = [hello_world, ionorb_wrapper, heatmapping]
        for function in functions:
            print(function) 
            gce = globus_compute_sdk.Executor(endpoint_id=settings["compute_endpoint"])

            params = []
            kwargs = {}
            if function == ionorb_wrapper:
                params= ["/eagle/IRIBeta/csimpson/fusion_ionorb_slice_tests/s164869",
                         "/eagle/IRIBeta/fusion/bin"]
            elif function == make_input_scripts:
                params= [os.path.join(settings["scratch_path"],"test_functions/make_input_scripts")]
                kwargs = {'shot':172578, 'stime':2600}
            elif function == heatmapping:
                params= [settings["bin_path"], 
                         os.path.join(settings["scratch_path"],"test_runs/test")]
            
            future = gce.submit(function,*params,**kwargs)
            print(future.result())
            
    else:
        print("Registering functions")
        functions = [make_input_scripts]#,make_plots,heatmapping,make_input_scripts]

        for function in functions:
            if args.function == "all" or args.function == function.__name__:
                register_function(function)
