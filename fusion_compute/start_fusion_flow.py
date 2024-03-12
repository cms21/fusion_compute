from fusion_compute.utils import get_specific_flow_client
from fusion_compute.machine_settings import machine_settings
from fusion_compute.flows import fusion_input
import globus_compute_sdk
from dotenv import load_dotenv
from fusion_compute import ENV_PATH
import os
import argparse

load_dotenv(dotenv_path=ENV_PATH)
client_id = os.getenv("CLIENT_ID")
flow_id = os.getenv("GLOBUS_FLOW_ID")

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


def run_flow(source_path, 
            return_path,
            destination_path = None,
            destination_relpath=None,
            inputs_function_kwargs={},
            machine="polaris", 
            dynamic=True, 
            label="ionorb-run", 
            tags=[], 
            flow_client=None,
            verbose=False):

    if destination_path is None and destination_relpath is None:
        raise Exception("No destination path set")

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
    
    flow_input = set_flow_input(machine, 
                                source_path,
                                return_path,
                                destination_path=destination_path,
                                destination_relpath=destination_relpath,
                                inputs_function_kwargs=inputs_function_kwargs,
                                verbose=verbose)
    if endpoint_status:

        if flow_client is None:
            collection_ids = [flow_input["input"]["destination"]["id"]]

            flow_client = get_specific_flow_client(flow_id=flow_id,
                                                   client_id=client_id,
                                                   collection_ids=collection_ids)
        label = machine+'_'+label
        if tags == None: tags = []
        tags+=[machine]
        
        flow_action = flow_client.run_flow(body=flow_input,
                                            label=label,
                                            tags=tags,)
        if verbose:
            print(f"Flow ID: {flow_action['flow_id']} \nFlow title: {flow_action['flow_title']} \nRun ID: {flow_action['run_id']} \nRun label: {flow_action['label']} \nRun owner: {flow_action['run_owner']}")
        print(f"run id: {flow_action['run_id']}")
        return flow_action['run_id']
    else:
        return None


def set_flow_input(machine,
                   source_path,
                   return_path, 
                   destination_path=None, 
                   destination_relpath=None, 
                   inputs_function_kwargs={}, 
                   verbose=False):

    flow_input = fusion_input

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
    
    # Set machine-specific flow inputs
    flow_input["input"]["inputs_endpoint_id"] = machine_settings["omega"]["compute_endpoint"]
    flow_input["input"]["inputs_function_kwargs"] = {"run_directory": source_path, 
                                                     **inputs_function_kwargs}
    flow_input["input"]["destination"]["id"] = settings["transfer_endpoint"]
    flow_input["input"]["compute_endpoint_id"] = settings["compute_endpoint"]
    flow_input["input"]["compute_function_kwargs"] = {"run_directory": run_directory, 
                                                      "bin_path": settings["bin_path"]}
    flow_input["input"]["plot_function_kwargs"] = {"run_directory": run_directory, 
                                                   "python_path": settings["bin_path"]}
    flow_input["input"]["source"]["outpath"] = return_path
    flow_input["input"]["source"]["path"] = source_path
    flow_input["input"]["destination"]["outpath"] = os.path.join(str(destination_path),"outputs/")
    flow_input["input"]["destination"]["path"] = destination_path

    # Set non-machine-specific flow inputs
    flow_input["input"]["compute_function_id"] = os.getenv("IONORB_FUNCTION_ID")
    flow_input["input"]["plot_function_id"] = os.getenv("HEATMAP_FUNCTION_ID")
    flow_input["input"]["inputs_function_id"] = os.getenv("INPUTS_FUNCTION_ID")
    flow_input["input"]["source"]["id"] = os.getenv("GLOBUS_TRANSFER_ENDPOINT_SRC")
    flow_input["input"]["recursive_tx"] = True
    
    if verbose:
        print(f"Compute function inputs={flow_input['input']['compute_function_kwargs']}")
        print(f"Plot function inputs={flow_input['input']['plot_function_kwargs']}")

    return flow_input

def arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--destination_path', default='/IRIBeta/fusion/test_runs/test/', help=f'Destination path for transfer file(s)')
    parser.add_argument('--source_path', default='/home/simpsonc/fusion', help=f'Path of file(s) to transfer')
    parser.add_argument('--destination_relpath', default=None, help=f'Destination path for transfer file(s) relative to base path')
    parser.add_argument('--return_path', default='/home/simpsonc/fusion_return/', help=f'Path where files are returned on source machine')
    parser.add_argument('--label', default='ionorb-run', help=f'Flow label')
    parser.add_argument('--tags', nargs="*", help=f'Flow tags')
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
    run = run_flow(args.input_json, 
             args.source_path, 
             args.return_path,
             destination_path=args.destination_path,
             destination_relpath=args.destination_relpath,
             inputs_function_kwargs={}, 
             machine=args.machine, 
             label=args.label,
             tags=args.tags,
             dynamic=args.dynamic,
             verbose=args.verbose)
    if args.verbose:
        print(run)
