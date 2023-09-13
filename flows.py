fusion_flow_definition = {
    "Comment": "Run Fusion application",
    "StartAt": "Transfer_to_Eagle",
    "States": {
        "Transfer_to_Eagle": {
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
            "Next": "MakePlots"
        },
        "MakePlots": {
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
            "Next": "Transfer_from_Eagle"
        },
        "Transfer_from_Eagle": {
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
        "compute_endpoint_id": None,
        "compute_function_id": None,
        "compute_function_kwargs": {},
        "plot_function_id": None,
        "plot_function_kwargs": {}
    }
}
