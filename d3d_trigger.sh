#!/bin/bash

# CMS: Add calls to run IDL scripts, something like this?
# ionorb_createB 164869 3005 EFIT01
# ionorb_create_birth 164869 3005 EFIT01 1 1 FULL 1000
# ionorb_generate_config

TIME_NOW=$(date +"%Y.%m.%d-%H%M%S")
SRC_PATH=/home/simpsonc/fusion/tmp_test
DEST_RELPATH=test_runs/$TIME_NOW
RET_PATH=/home/simpsonc/fusion_return/$TIME_NOW
MACHINE="polaris"
DYNAMIC=""
i=1
if [ $# -gt 0 ]; then
	while [ $i -le $# ]; do
		if [ $1 == "--dynamic" ]; then
			DYNAMIC="--dynamic"
		fi
		if [ $1 == "--machine" ]; then
			shift 1
			if [[ $1 = "polaris" || $1 = "perlmutter" || $1 = "summit" ]]; then
	    		MACHINE=$1
			else
				echo Machine not recognized
			fi
    	fi
		shift 1
	done
fi

python fusion_compute/start_fusion_flow.py --machine $MACHINE $DYNAMIC \
							--source_path $SRC_PATH \
							--destination_relpath $DEST_RELPATH \
							--return_path $RET_PATH \
							--tags $TIME_NOW
