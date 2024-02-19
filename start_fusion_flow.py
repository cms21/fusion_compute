from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os, json
import argparse

load_dotenv(dotenv_path="./fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")

machine_settings = {"polaris":{"transfer_endpoint": os.getenv("GLOBUS_ALCF_EAGLE"),
                                   "compute_endpoint": os.getenv("GLOBUS_COMPUTE_POLARIS_ENDPOINT"),
                                   "bin_path": "/eagle/IRIBeta/fusion/bin",
                                   "scratch_path": "/IRIBeta/fusion/",
                                   "facility": "alcf"},
                    "perlmutter":{"transfer_endpoint": os.getenv("GLOBUS_NERSC_PERLMUTTER"),
                                    "compute_endpoint": os.getenv("GLOBUS_COMPUTE_PERLMUTTER_ENDPOINT"),
                                    "bin_path": "/global/common/software/m3739/perlmutter/ionorb/bin/",
                                    "scratch_path": "/pscratch/sd/c/csimpson", ### User needs to change this!
                                    "facility": "nersc"},
                    "summit":{"transfer_endpoint": os.getenv("GLOBUS_OLCF"),
                              "compute_endpoint": os.getenv("GLOBUS_COMPUTE_SUMMIT_ENDPOINT"),
                              "bin_path": "/ccs/home/simpson/bin/",
                               "scratch_path": "/gpfs/alpine/gen008/scratch/simpson/", ### User needs to change this!
                               "facility": "olcf"},
                    "omega":{"transfer_endpoint": os.getenv("GLOBUS_D3D"),
                              "compute_endpoint": os.getenv("GLOBUS_COMPUTE_OMEGA_LOCAL_ENDPOINT"),
                              "bin_path": "/fusion/projects/codes/ionorb/bin",
                               "scratch_path": "/home/simpsonc", ### User needs to change this!
                               "facility": "d3d"}}

def endpoint_active(compute_endpoint_id):
    gc = globus_compute_sdk.Client()
    endpoint_status = gc.get_endpoint_status(compute_endpoint_id)['status']
    endpoint_metadata = gc.get_endpoint_metadata(compute_endpoint_id)
    if endpoint_status != 'online':
        print(f"Endpoint {endpoint_metadata['name']} is {endpoint_status}")
        print(f"Login into {endpoint_metadata['hostname']} and restart endpoint")
        return False
    else:
        return True
    
def check_username(machine,verbose=False):
    facility = machine_settings[machine]["facility"]
    ret=os.popen(f"globus whoami --linked-identities | grep {facility}").read()
    if verbose:
        print(f"check username for {machine}")
        print(f"{ret}")
    if facility in ret:
        return ret.split("@")[0]
    else:
        print(f"WARNING: Auth not yet established for {machine}")
        return None
    
def run_flow(input_json, source_path, destination_path, return_path, machine="polaris", destination_relpath=None, dynamic=True, label=None, tags=None, flow_client=None,verbose=False):
    
    endpoint_status = endpoint_active(machine_settings[machine]["compute_endpoint"])
    if dynamic and endpoint_status == False and destination_relpath != None:
        for alternate_machine in machine_settings.keys():
            if alternate_machine == machine:
                continue
            endpoint_status = endpoint_active(machine_settings[alternate_machine]["compute_endpoint"])
            if endpoint_status:
                print(f"Switching to machine {alternate_machine} instead")
                machine = alternate_machine
                break
    
    flow_input = set_flow_input(machine, input_json,source_path,destination_path,return_path,destination_relpath=destination_relpath,verbose=verbose)
    if endpoint_status:
        if flow_client is None:
            flow_client = create_flows_client()
        flow = flow_client.get_flow(flow_id)
        flow_scope = flow['globus_auth_scope']
        flow_action = flow_client.run_flow(flow_id, flow_scope, flow_input, label=label, tags=tags)
        if verbose:
            print(f"Flow ID: {flow_action['flow_id']} \nFlow title: {flow_action['flow_title']} \nRun ID: {flow_action['run_id']} \nRun label: {flow_action['label']} \nRun owner: {flow_action['run_owner']}")        
        return flow_action
    else:
        return None

def set_flow_input(machine, input_json,source_path,destination_path,return_path,destination_relpath=None, verbose=False):

    flow_input = json.load(open(input_json))

    settings = machine_settings[machine]

    # If destination_relpath is set, override destination_path
    if destination_relpath != None:
        if verbose:
            print(f"Using destination_relpath")
        destination_path = os.path.join(settings["scratch_path"],destination_relpath)
    run_directory = destination_path

    # Machine specific special cases
    if machine == "polaris":
        run_directory = os.path.join("/eagle","/".join(str(destination_path).split("/")[1:]))    
    # if machine == "perlmutter" and destination_relpath != None:
    #     username = check_username(machine,verbose=verbose)
    #     if verbose:
    #         print(f"username: {username}")
    #     if username != None:
    #         destination_path = os.path.join(settings["scratch_path"],username[0],username,destination_relpath)
    #         run_directory = destination_path
    #     else:
    #         raise Exception("Need to establish username for nersc to use destination_relpath; try running without destination_relpath first to establish auth")
    
    # Set flow inputs
    flow_input["input"]["inputs_endpoint_id"] = machine_settings["omega"]["compute_endpoint"]
    flow_input["input"]["inputs_function_kwargs"] = {"run_directory": source_path}
    flow_input["input"]["destination"]["id"] = settings["transfer_endpoint"]
    flow_input["input"]["compute_endpoint_id"] = settings["compute_endpoint"]
    flow_input["input"]["compute_function_kwargs"] = {"run_directory": run_directory}
    flow_input["input"]["plot_function_kwargs"] = {"run_directory": run_directory, 
                                                   "python_path": settings["bin_path"]}
    flow_input["input"]["source"]["outpath"] = return_path
    flow_input["input"]["source"]["path"] = source_path
    flow_input["input"]["destination"]["outpath"] = os.path.join(str(destination_path),"outputs/")
    flow_input["input"]["destination"]["path"] = destination_path
    flow_input["input"]["recursive_tx"] = True
    
    if verbose:
        print(f"Compute function inputs={flow_input['input']['compute_function_kwargs']}")
        print(f"Plot function inputs={flow_input['input']['plot_function_kwargs']}")

    return flow_input

def arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--destination_path', default='/IRIBeta/fusion/test_runs/test/', help=f'Destination path for transfer file(s)')
    parser.add_argument('--source_path', default='/csimpson/polaris/fusion/', help=f'Path of file(s) to transfer')
    parser.add_argument('--destination_relpath', default=None, help=f'Destination path for transfer file(s) relative to base path')
    parser.add_argument('--return_path', default='/csimpson/polaris/fusion_return/', help=f'Path where files are returned on source machine')
    parser.add_argument('--label', default='transfer-fusion-run', help=f'Flow label')
    parser.add_argument('--tags', default={}, help=f'Flow label')
    parser.add_argument('--machine', default='polaris', help=f'Target machine for flow', choices=machine_settings.keys())
    parser.add_argument('--input_json', help='Path to the flow input .json file',
                        default="./input.json")
    parser.add_argument('--verbose', default=False, action='store_true', help=f'Verbose output')
    parser.add_argument('--dynamic', default=False, action='store_true', help=f'Dynamically choose available machine')

    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()
    if args.verbose:
        print(f"Running flow {flow_id}")
        print(f"Running on {args.machine}")
        print(f"Path on source endpoint is {args.source_path}")
        print(f"Path on destination endpoint is {args.destination_path}")
        print(f"Path on local machine to input.json is {args.input_json}")
        print(f"Flow label {args.label}")
    run_flow(args.input_json, 
             args.source_path, 
             args.destination_path, 
             args.return_path, 
             machine=args.machine, 
             label=args.label,
             destination_relpath=args.destination_relpath,
             dynamic=args.dynamic,
            verbose=args.verbose)
