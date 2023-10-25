# from globus_automate_client import create_flows_client
from get_flow_client import get_flows_client
from dotenv import load_dotenv
from flows import heatmap_flow_definition as fusion_flow_definition
from flows import fusion_input
import os
import json
import subprocess
from globus_cli.login_manager import LoginManager

load_dotenv(dotenv_path="./fusion.env")

if __name__ == '__main__':

    # Get registered funcion
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

    # Get flow
    flow_id = os.getenv("GLOBUS_FLOW_ID")
    #fc = create_flows_client()
    #fc = get_flows_client()
    login_manager = LoginManager()
    fc = login_manager.get_flows_client()

    # If the flow has not yet been created, deploy new flow
    if flow_id is None:
        print("Creating new flow")
        #flow = fc.deploy_flow(fusion_flow_definition, title="Fusion flow", input_schema={})
        flow = fc.create_flow(definition=fusion_flow_definition, title="Fusion flow", input_schema={})
        flow_id = flow['id']
        with open("fusion.env", "a") as f:
            f.write(f"# Function that executes fusion_wrapper\n")
            f.write(f"GLOBUS_FLOW_ID={flow_id}\n")
    # If the flow has been created, check to see if the flow has been updated and update if necessary
    else:
        flow = fc.get_flow(flow_id)
        if flow['definition'] != fusion_flow_definition:
            fc.update_flow(flow_id, definition=fusion_flow_definition)
            print("Updated flow defintion")

    print(f"flow_id = '{flow_id}'")

    # Create input file with the correct ids for endpoints and functions
    fusion_input["input"]["compute_function_id"] = os.getenv("IONORB_FUNCTION_ID")
    fusion_input["input"]["plot_function_id"] = os.getenv("HEATMAP_FUNCTION_ID")

    fusion_input["input"]["source"]["id"] = os.getenv("GLOBUS_TRANSFER_ENDPOINT_SRC")

    # Write flow inputs file
    with open("input.json", "w") as file:
        json.dump(fusion_input, file)
