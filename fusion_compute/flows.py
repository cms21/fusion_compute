# Basic flow that has these steps:
# 1. Transfer from machine A to machine B
# 2. Run ionorb on machine B
# 3. Transfer results from machine B to machine A
basic_flow_definition = {
    "Comment": "Run Fusion application",
    "StartAt": "Transfer_In",
    "States": {
        "Transfer_In": {
            "Comment": "Transfer files",
            "Type": "Action",
            "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
            "Parameters": {
                "notify_on_succeeded": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
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
            "ResultPath": "$.TransferInOutput",
            "WaitTime": 300,
            "Next": "IonOrb"
        },
        "IonOrb": {
            "Comment": "IonOrb",
            "Type": "Action",
            "ActionUrl": "https://compute.actions.globus.org",
            "Parameters": {
                "endpoint.$": "$.input.compute_endpoint_id",
                "function.$": "$.input.compute_function_id",
                "kwargs.$": "$.input.compute_function_kwargs"
            },
            "ResultPath": "$.IonOrbOutput",
            "WaitTime": 86400,
            "Next": "Transfer_Out"
        },
        "Transfer_Out": {
            "Comment": "Transfer outfile",
            "Type": "Action",
            "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
            "Parameters": {
                "notify_on_succeeded": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
                "source_endpoint_id.$": "$.input.destination.id",
                "destination_endpoint_id.$": "$.input.source.id",
                "transfer_items": [
                    {
                        "source_path.$": "$.input.destination.outpath",
                        "destination_path.$": "$.input.source.outpath",
                        "recursive": True
                    }
                ]
            },
            "ResultPath": "$.TransferOutOutput",
            "WaitTime": 300,
            "End": True
        }
    }
}


# Flow that runs ionorb and postprocessing script (e.g. heatmap). 
# Has 6 steps:
# 0. Make inputs
# 1. Check if the birth file contains particles, only proceed if particle number is not 0
# 2. Transfer from machine A to machine B
# 3. Run ionorb on machine B
# 4. Run postprocessing application such as heatmap python routine on machine B
# 5. Transfer results of ionorb and postprocessing from machine B to machine A
inputs_flow_definition = {
    "Comment": "Run Fusion application",
    "StartAt": "Make_Inputs",
    "States": {
        "Make_Inputs": {
                "Comment": "Make Inputs",
                "Type": "Action",
                "ActionUrl": "https://compute.actions.globus.org",
                "Parameters": {
                    "endpoint.$": "$.input.inputs_endpoint_id",
                    "function.$": "$.input.inputs_function_id",
                    "kwargs.$": "$.input.inputs_function_kwargs"
                },
                "ResultPath": "$.MakeInputsOutput",
                "WaitTime": 86400,
                "Next": "ProceedChoice"
            },
        "ProceedChoice": {
            "Comment": "Proceed Choice",
            "Type": "Choice",
            "Choices": [{
                "Variable": "$.MakeInputsOutput.details.result[0][2]",
                "StringEquals": "0",
                "Next": "EndState"
                 },],
            "Default": "Transfer_In",
        },
        "Transfer_In": {
            "Comment": "Transfer files",
            "Type": "Action",
            "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
            "Parameters": {
                "notify_on_succeeded": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
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
            "ResultPath": "$.TransferInOutput",
            "WaitTime": 300,
            "Next": "IonOrb"
        },
        "IonOrb": {
            "Comment": "IonOrb",
            "Type": "Action",
            "ActionUrl": "https://compute.actions.globus.org",
            "Parameters": {
                "endpoint.$": "$.input.compute_endpoint_id",
                "function.$": "$.input.compute_function_id",
                "kwargs.$": "$.input.compute_function_kwargs"
            },
            "ResultPath": "$.IonOrbOutput",
            "WaitTime": 86400,
            "Next": "Postprocessing"
        },
        "Postprocessing": {
            "Comment": "Make plots",
            "Type": "Action",
            "ActionUrl": "https://compute.actions.globus.org",
            "Parameters": {
                "endpoint.$": "$.input.compute_endpoint_id",
                "function.$": "$.input.plot_function_id",
                "kwargs.$": "$.input.plot_function_kwargs"
            },
            "ResultPath": "$.PlotsOutput",
            "WaitTime": 86400,
            "Next": "Transfer_Out"
        },
        "Transfer_Out": {
            "Comment": "Transfer outfile",
            "Type": "Action",
            "ActionUrl": "https://actions.automate.globus.org/transfer/transfer",
            "Parameters": {
                "notify_on_succeeded": False,
                "notify_on_failed": True,
                "notify_on_inactive": True,
                "source_endpoint_id.$": "$.input.destination.id",
                "destination_endpoint_id.$": "$.input.source.id",
                "transfer_items": [
                    {
                        "source_path.$": "$.input.destination.outpath",
                        "destination_path.$": "$.input.source.outpath",
                        "recursive": True
                    }
                ]
            },
            "ResultPath": "$.TransferOutOutput",
            "WaitTime": 300,
            "Next": "EndState"
        },
        "EndState": {
            "Comment": "End state",
            "Type": "Pass",
            "ResultPath": "$.EndStateOutput",
            "End": True
        },
    }
}

# Inputs for flows
fusion_input = {
    "input": {
        "source": {
            "path": None,
            "id": None,
            "outpath": None,
        },
        "destination": {
            "path": None,
            "id": None,
            "outpath": None,
        },
        "recursive_tx": None,
        "inputs_endpoint_id": None,
        "inputs_function_id": None,
        "inputs_function_kwargs": {},
        "compute_endpoint_id": None,
        "compute_function_id": None,
        "compute_function_kwargs": {},
        "plot_function_id": None,
        "plot_function_kwargs": {}
    }
}
