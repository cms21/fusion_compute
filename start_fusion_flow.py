from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os, json
import argparse

load_dotenv(dotenv_path="./fusion.env")
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
    
def run_flow(input_json, source_path, destination_path, return_path, label=None, tags=None, flow_client=None,verbose=False):
    
    flow_input = set_flow_input(input_json,source_path,destination_path,return_path,verbose=verbose)
    if endpoint_active(flow_input["input"]["compute_endpoint_id"]):
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


def set_flow_input(input_json,source_path,destination_path,return_path,verbose=False):

    flow_input = json.load(open(input_json))
    flow_input["input"]["source"]["outpath"] = return_path
    flow_input["input"]["source"]["path"] = source_path
    flow_input["input"]["destination"]["outpath"] = os.path.join(destination_path,"outputs/")
    flow_input["input"]["destination"]["path"] = destination_path
    flow_input["input"]["recursive_tx"] = True
    flow_input["input"]["compute_function_kwargs"] = {"run_directory": os.path.join("/eagle","/".join(destination_path.split("/")[1:]))}
    flow_input["input"]["plot_function_kwargs"] = {"run_directory": os.path.join("/eagle","/".join(destination_path.split("/")[1:]))}
    
    if verbose:
        print(f"Compute function inputs={flow_input['input']['compute_function_kwargs']}")
        print(f"Plot function inputs={flow_input['input']['plot_function_kwarg']}")

    return flow_input

def arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--destination_path', default='/IRIBeta/test_runs/', help=f'Destination path for transfer file(s)')
    parser.add_argument('--source_path', default='/csimpson/polaris/fusion/', help=f'Path of file(s) to transfer')
    parser.add_argument('--return_path', default='/csimpson/polaris/fusion_return/', help=f'Path where files are returned on source machine')
    parser.add_argument('--label', default='transfer-fusion-run', help=f'Flow label')
    parser.add_argument('--input_json', help='Path to the flow input .json file',
                        default="./input.json")
    parser.add_argument('--verbose', default=False, action='store_true', help=f'Verbose output')

    return parser.parse_args()

if __name__ == '__main__':

    args = arg_parse()
    if args.verbose:
        print(f"Running flow {flow_id}")
        print(f"Path on source endpoint is {args.source_path}")
        print(f"Path on destination endpoint is {args.destination_path}")
        print(f"Path on local machine to input.json is {args.destination_path}")
        print(f"Flow label {args.source_path}")
    run_flow(args.input_json, args.source_path, args.destination_path, args.return_path, label=args.label, verbose=args.verbose)
