from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os, json

load_dotenv(dotenv_path="./fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")
fusion_func = os.getenv("GLOBUS_FUNCTION_ID")
compute_endpoint = os.getenv("GLOBUS_COMPUTE_ENDPOINT")

fusion_flow_definition = {
    "Comment": "Run Fusion application",
    "StartAt": "Fusion",
    "States": {
        "Fusion": {
            "Comment": "Fusion",
            "Type": "Action",
            "ActionUrl": "https://compute.actions.globus.org",
            "Parameters": {
                "endpoint.$": "$.input.compute_endpoint_id",
                "function.$": "$.input.compute_function_id",
                "kwargs.$": "$.input.compute_function_kwargs"
            },
            "ResultPath": "$.FusionOutput",
            "WaitTime": 600,
            "End": True
        }
    }
}

fusion_input = {
    "input": {
      "compute_endpoint_id": None,
      "compute_function_id": None,
      "compute_function_kwargs": {}
    }
}

def fusion_wrapper(input_str="Hello Iris"):
    import subprocess
    
    cmd = f"echo {input_str}" 
    res = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")


if __name__ == '__main__':

    # Get registered funcion
    gc = globus_compute_sdk.Client()
    if fusion_func is None:
        print("Registering new function")
        fusion_func = gc.register_function(fusion_wrapper)
        with open("fusion.env","a") as f:
            f.write(f"GLOBUS_FUNCTION_ID={fusion_func}\n")

    print(f"function_id = '{fusion_func}'")

    # Get flow
    fc = create_flows_client()
    if flow_id is None:
        print("Creating new flow")
        flow = fc.deploy_flow(fusion_flow_definition, title="Fusion flow", input_schema={})
        flow_id = flow['id']
        with open("fusion.env","a") as f:
            f.write(f"GLOBUS_FLOW_ID={flow_id}\n")
    else:
        flow = fc.get_flow(flow_id)
        if flow['definition'] != fusion_flow_definition:
            fc.update_flow(flow_id,flow_definition=fusion_flow_definition)
            print(f"Updated flow defintion")
            print(fusion_flow_definition)

    print(f"flow_id = '{flow_id}'")

    # Create input file with the correct ids
    fusion_input["input"]["compute_endpoint_id"] = compute_endpoint
    fusion_input["input"]["compute_function_id"] = fusion_func

    with open("input.json","w") as file:
        json.dump(fusion_input,file)


   