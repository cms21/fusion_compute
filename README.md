# fusion_compute
Scripts to deploy fusion application on ALCF systems with Globus Flows

## Setup on Polaris/Perlmutter
First login to Polaris and/or Perlmutter and do the following things:
### 1. Load conda module

On Polaris:
```
module load conda
conda activate /eagle/IRIBeta/fusion/fusion_env
```

### 2. Create a Globus Endpoint
Use the provided `<MACHINE>_config.yml_template` as a model to configure your endpoint in the [endpoint_configs](endpoint_configs) directory. Edit it to replace your project name, environment name, etc.  Then do:

```
globus-compute-endpoint configure --endpoint-config config.yml_template <YOUR_ENDPOINT_NAME>
globus-compute-endpoint start <YOUR_ENDPOINT_NAME>
globus-compute-endpoint list
```

Copy the endpoint ID for the next step.

## Setup on Iris
### 1. Clone this repo
Clone this repo. Paste your compute enpoint IDs for Polaris and/or Perlmutter into `fusion.env_template` and copy it to `fusion.env`.  Also paste in the source endpoint id into the file.

```
cp fusion.env_template fusion.env
```
### 2. Make an environment and install globus

Make a conda environment.
```
module load conda/py3.9-spyder
conda create -n globus python=3.9
conda activate globus
```
Install required packages.
```
conda install globus-compute-sdk globus-automate-client globus-cli python-dotenv 
```

### 3. Run the setup script
```
python setup_fusion_flow.py
```

When running this script for the first time, you will be asked to authenticate your ALCF credentials with globus.  Running this script should create a new file `input.json` and modify `fusion.env` by adding some new environment variables containing the IDs of the flow and functions.

Login to globus.  You will be directed to a web page to validate your globus credentials.
```
globus login
```

### 4. Run the flow

You can start a flow by using the python script:
```
python start_fusion_flow.py --source_path <SRC_PATH> --destination_path <DEST_PATH> --return_path <RET_PATH>
```
You will be prompted to validate your globus credentials the first time you run this script.  Additionally, you may recieve an email from the Globus service saying your flow "requires attention".  If you do recieve this email, follow its instructions for resuming the flow from the CLI (it will be a command that starts with `globus-automate`).  After validating your credentials for this first run, you should not have to validate again (or not for a longish period of time).

The path `<SRC_PATH>` and `<RET_PATH>` should be paths on the source machine and `<DEST_PATH>` should be a path on the destination machine (eagle).

### 5. Trigger Script

There's a trigger bash script that wraps around `start_fusion_flow.py`, [iris_trigger.sh](iris_trigger.sh).  This could be used to bundle the flow with the local execution of IDL scripts.

### 6. Tutorial Notebook

There's a Jupyter notebook [Fusion_tutorial_example.ipynb](Fusion_tutorial_example.ipynb) that runs a simplified flow and breaks down how to deploy it with explanations.
