from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os
import json

load_dotenv(dotenv_path="./fusion.env")

fusion_flow_definition = {
    "Comment": "Run Fusion application",
    "StartAt": "TransferFiles",
    "States": {
        "TransferFiles": {
            "Comment": "Transfer files",
            "Type": "Action",
            "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
            "Parameters": {
                "source_endpoint_id.$": "$.input.source.id",
                "destination_endpoint_id.$": "$.input.destination.id",
                "transfer_items": [
                    {
                        "source_path.$": "$.input.source.path",
                        "destination_path.$": "$.input.destination.path",
                        "recursive.$": "$.input.recursive_tx"
                    }
                ]
            },
            "ResultPath": "$.TransferFiles",
            "WaitTime": 300,
            "Next": "Fusion"
        },
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
            "WaitTime": 86400,
            "End": True
        }
    }
}

fusion_input = {
    "input": {
        "source": {
            "path": None,
            "id": None,
        },
        "destination": {
            "path": None,
            "id": None,
        },
        "recursive_tx": None,
        "compute_endpoint_id": None,
        "compute_function_id": None,
        "compute_function_kwargs": {}
    }
}

# Application that returns stdout to Globus service
def fusion_wrapper(input_str="Hello Iris"):
    import subprocess

    cmd = f"echo {input_str}"
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash')
    return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")

# Application that returns stdout to Globus service
def fusion_wrapper_sleep(input_str="Hello Iris", sleep_time=0):
    import subprocess

    cmd = f"echo {input_str}; sleep {sleep_time}"
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash')
    if res.returncode != 0:
        raise Exception(f"Application failed with non-zero return code")
  
    return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")

# Application that returns stdout to file on compute machine file system
def fusion_stdout_file_wrapper(input_str="Hello Iris", proc_dir="/eagle/datascience/csimpson/fusion/dummy_data/"):
    import subprocess
    import os

    cmd = f"echo {input_str}"
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, executable='/bin/bash')

    with open(os.path.join(proc_dir,'output.log'), 'w+') as f:
        f.write(res.stdout.decode('utf-8'))

    with open(os.path.join(proc_dir,'errors.log'), 'w+') as f:
        f.write(res.stderr.decode('utf-8'))

    return res.returncode


if __name__ == '__main__':

    # Get registered funcion
    fusion_func = os.getenv("GLOBUS_FUNCTION_ID")
    if fusion_func is None:
        gc = globus_compute_sdk.Client()
        print("Registering new function")
        fusion_func = gc.register_function(fusion_wrapper_sleep)
        with open("fusion.env", "a") as f:
            f.write(f"GLOBUS_FUNCTION_ID={fusion_func}\n")

    print(f"function_id = '{fusion_func}'")

    # Get flow
    flow_id = os.getenv("GLOBUS_FLOW_ID")
    fc = create_flows_client()
    if flow_id is None:
        print("Creating new flow")
        flow = fc.deploy_flow(fusion_flow_definition, title="Fusion flow", input_schema={})
        flow_id = flow['id']
        with open("fusion.env", "a") as f:
            f.write(f"GLOBUS_FLOW_ID={flow_id}\n")
    else:
        flow = fc.get_flow(flow_id)
        if flow['definition'] != fusion_flow_definition:
            fc.update_flow(flow_id, flow_definition=fusion_flow_definition)
            print("Updated flow defintion")
            print(fusion_flow_definition)

    print(f"flow_id = '{flow_id}'")

    # Create input file with the correct ids
    fusion_input["input"]["compute_endpoint_id"] = os.getenv("GLOBUS_COMPUTE_ENDPOINT")
    fusion_input["input"]["compute_function_id"] = fusion_func

    fusion_input["input"]["source"]["id"] = os.getenv("GLOBUS_TRANSFER_ENDPOINT_SRC")
    fusion_input["input"]["destination"]["id"] = os.getenv("GLOBUS_TRANSFER_ENDPOINT_DEST")

    # fusion_input["input"]["source"]["id"] = source_path
    # fusion_input["input"]["destination"]["id"] = destination_path
    # fusion_input["input"]["recursive_tx"] = False

    with open("input.json", "w") as file:
        json.dump(fusion_input, file)
