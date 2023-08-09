from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os, json, time, uuid
import argparse

load_dotenv(dotenv_path="../fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")

def endpoint_active(flow_input):
    gc = globus_compute_sdk.Client()
    endpoint_id = flow_input["input"]["compute_endpoint_id"]
    endpoint_status = gc.get_endpoint_status(endpoint_id)['status']
    endpoint_metadata = gc.get_endpoint_metadata(endpoint_id)
    if endpoint_status != 'online':
        print(f"Endpoint {endpoint_metadata['name']} is {endpoint_status}")
        print(f"Login into {endpoint_metadata['hostname']} and restart endpoint")
        return False
    else:
        return True
    
def run_flow(flow_input,label=None, tags=None, flow_client=None,verbose=False):

    if endpoint_active(flow_input):
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

def arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--destination_path', default='/datascience/csimpson/fusion/dummy_data/dummy.txt', help=f'Destination path for transfer file(s)')
    parser.add_argument('--source_path', default='/csimpson/polaris/fusion/dummy.txt', help=f'Path of file(s) to transfer')
    parser.add_argument('--recursive', default=False, help=f'Do recursive file transfer')
    parser.add_argument('--label', default='transfer-fusion-run', help=f'Flow label')
    parser.add_argument('--input_json', help='Path to the flow input .json file',
                        default='../input.json')
    parser.add_argument('--verbose', default=False, action='store_true', help=f'Verbose output')

    return parser.parse_args()


if __name__ == '__main__':

    args = arg_parse()

    flow_input = json.load(open(args.input_json))
    label = args.label

    flow_input["input"]["recursive_tx"] = args.recursive
    flow_input['input']['source']['path'] = args.source_path
    flow_input['input']['destination']['path'] = args.destination_path

    run_flow(flow_input, label=label, verbose=args.verbose)