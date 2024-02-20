from utils import get_flows_client, get_specific_flow_client
from dotenv import load_dotenv
from flows import heatmap_flow_definition as fusion_flow_definition
from flows import fusion_input
import os
import json
import subprocess
import argparse

load_dotenv(dotenv_path="./fusion.env")

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset-scopes', default=False, action='store_true', help=f'Verbose output')
    return parser.parse_args()

if __name__ == '__main__':

    # reset_scopes will replace the ~/.sdk-manage-flow.json file
    args = arg_parse()
    reset_scopes = args.reset_scopes

    # Get project client id
    client_id = os.getenv("CLIENT_ID")

    # Register Functions
    fusion_func = os.getenv("IONORB_FUNCTION_ID")
    if fusion_func is None:
        ret = subprocess.run("python functions.py --function ionorb_wrapper".split())
        load_dotenv(dotenv_path="./fusion.env")
        fusion_func = os.getenv("IONORB_FUNCTION_ID")
    print(f"ionorb function_id = '{fusion_func}'")

    fusion_func = os.getenv("HEATMAP_FUNCTION_ID")
    if fusion_func is None:
        ret = subprocess.run("python functions.py --function heatmapping".split())
        load_dotenv(dotenv_path="./fusion.env")
        fusion_func = os.getenv("HEATMAP_FUNCTION_ID")
    print(f"heatmap function_id = '{fusion_func}'")

    # Register Flow
    flow_id = os.getenv("GLOBUS_FLOW_ID")
    fc = get_flows_client(client_id=client_id)

    # If the flow has not yet been created, deploy new flow
    if flow_id is None:

        print("Creating new flow")
        flow = fc.create_flow(definition=fusion_flow_definition, title="Fusion flow", input_schema={})
        flow_id = flow['id']
        reset_scopes = True
        with open("fusion.env", "a") as f:
            f.write(f"# Function that executes fusion_wrapper\n")
            f.write(f"GLOBUS_FLOW_ID={flow_id}\n")

    # If the flow has already been created, update the flow
    else:
        flow = fc.get_flow(flow_id)
        if flow['definition'] != fusion_flow_definition:
            fc.update_flow(flow_id, definition=fusion_flow_definition)
            print("Updated flow defintion")

    print(f"flow_id = '{flow_id}'")

    # Add collections to flow scope
    # D3D endpoint not included here because it is a personal collection currently
    if reset_scopes:

        if os.path.exists("~/.sdk-manage-flow.json"):
            os.remove("~/.sdk-manage-flow.json")
        collection_ids = [eid for eid in [os.getenv("GLOBUS_ALCF_EAGLE"),
                                          os.getenv("GLOBUS_NERSC_PERLMUTTER"),
                                          os.getenv("GLOBUS_OLCF")]
                                          if eid != None]
        print(f"Adding {collection_ids} to flow scope")
        sfc = get_specific_flow_client(flow_id=flow_id,
                                       client_id=client_id,
                                       collection_ids=collection_ids)

    # Create input file with the correct ids for endpoints and functions
    fusion_input["input"]["compute_function_id"] = os.getenv("IONORB_FUNCTION_ID")
    fusion_input["input"]["plot_function_id"] = os.getenv("HEATMAP_FUNCTION_ID")

    fusion_input["input"]["source"]["id"] = os.getenv("GLOBUS_TRANSFER_ENDPOINT_SRC")

    # Write flow inputs file
    with open("input.json", "w") as file:
        json.dump(fusion_input, file)
