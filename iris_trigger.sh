#!/bin/bash

# Ensure these modules are loaded before running this script:
# module load conda/py3.9-spyder
# conda activate fusion
# module load ionorbgpu/birth

# CMS: Add calls to run IDL scripts, something like this?
# ionorb_createB 164869 3005 EFIT01
# ionorb_create_birth 164869 3005 EFIT01 1 1 FULL 1000
# ionorb_generate_config

TIME_NOW=$(date +"%Y.%m.%d-%H%M%S")
SRC_PATH=/csimpson/polaris/fusion
DEST_PATH=/IRIBeta/test_runs/$TIME_NOW
RET_PATH=/csimpson/polaris/fusion_return/$TIME_NOW
echo Return path is $RET_PATH
python start_fusion_flow.py --source_path $SRC_PATH --destination_path $DEST_PATH --return_path $RET_PATH --label "iris_trigger_flow"