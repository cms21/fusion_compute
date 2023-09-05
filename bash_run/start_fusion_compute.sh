#!/bin/bash

export $(grep -v '^#' ../fusion.env | xargs)

recursive_tx=False # set false to copy a file, true for a directory
source_path="/csimpson/polaris/fusion/dummy.txt"
destination_path="/datascience/csimpson/fusion/dummy_data/dummy.txt"

hello_string="Hello Oberon"
sleep_time=-5

flow_input="{"input": {"source": {"path": "$source_path", 
                                    "id": "$GLOBUS_TRANSFER_ENDPOINT_SRC"}, 
                        "destination": {"path": "$destination_path", 
                                        "id": "$GLOBUS_TRANSFER_ENDPOINT_DEST"}, 
                        "recursive_tx": "$recursive_tx", 
                        "compute_endpoint_id": "$GLOBUS_COMPUTE_ENDPOINT", 
                        "compute_function_id": "$GLOBUS_FUNCTION_ID", 
                        "compute_function_kwargs": {"input_str": "$hello_string",
                                                    "sleep_time": "$sleep_time"}}}"


globus-automate flow run --flow-input "$flow_input" $GLOBUS_FLOW_ID --label fusion-flow
