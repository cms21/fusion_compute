# fusion_compute
Scripts to deploy fusion application on ALCF systems with Globus Flows

## Setup on Polaris/Perlmutter
First login to Polaris and/or Perlmutter and do the following things:
### 1. Load conda module

On Polaris:
```bash
module load conda
conda activate /eagle/IRIBeta/fusion/fusion_env
```

### 2. Create a Globus Endpoint
Use the provided `<MACHINE>_config.yml_template` as a model to configure your endpoint in the [endpoint_configs](endpoint_configs) directory. Edit it to replace your project name, environment name, etc.  Then do:

```bash
globus-compute-endpoint configure --endpoint-config config.yml_template <YOUR_ENDPOINT_NAME>
globus-compute-endpoint start <YOUR_ENDPOINT_NAME>
globus-compute-endpoint list
```

Copy the endpoint ID for the next step.

## Setup on Iris
### 1. Clone this repo
Clone this repo. Paste your compute enpoint IDs for Polaris and/or Perlmutter into `fusion.env_template` and copy it to `fusion.env`.  Also paste in the source endpoint id into the file.

```bash
cp fusion.env_template fusion.env
```
### 2. Make an environment and install globus

Make a conda environment.
```bash
module load conda/py3.9-spyder
conda create -n globus python=3.9
conda activate globus
```
Install required packages.
```bash
conda install globus-compute-sdk globus-automate-client globus-cli python-dotenv 
```

### 3. Run the setup script
```bash
python setup_flow.py
```

When running this script for the first time, you will be asked to authenticate your ALCF credentials with globus.  Running this script should create a new file `input.json` and modify `fusion.env` by adding some new environment variables containing the IDs of the flow and functions.

Login to globus.  You will be directed to a web page to validate your globus credentials.
```bash
globus login
```

### 4. Run the flow

You can start a flow by using the python script:
```bash
python start_fusion_flow.py --source_path <SRC_PATH> --destination_path <DEST_PATH> --return_path <RET_PATH>
```
You will be prompted to validate your globus credentials the first time you run this script.  Additionally, you may recieve an email from the Globus service saying your flow "requires attention".  If you do recieve this email, restart the flow from the same CLI with this command `globus-automate flow run-resume --query-for-inactive-reason --flow-id <FLOW_ID> <RUN_ID>`.  Currently, this code base uses the `globus-automate` client so you need to use the `globus-automate` CLI call; the email you recieve will give you a command that starts with `globus flows` but do not use this, as it assumes a different type of client.  We will be updating this repository to use the newer globus client, but until that change has been made use the `globus-automate` CLI tool.  This email will include the `RUN_ID`.  After validating your credentials for this first run with the `globus-automate` tool, you should not have to validate again.

The path `<SRC_PATH>` and `<RET_PATH>` should be paths on the source machine and `<DEST_PATH>` should be a path on the destination machine (eagle).

### 5. Trigger Script

There's a trigger bash script that wraps around `start_fusion_flow.py`, [iris_trigger.sh](iris_trigger.sh).  This could be used to bundle the flow with the local execution of IDL scripts.

You can run the trigger script like this
```bash
iris_trigger.sh --machine <MACHINE> --dynamic
```
If you include the --machine option, the flow will attempt to run on that machine.  If it is not included, it will try to run on Polaris.  If `--dynamic` is included, the agent will adapt to run on a different machine if the first-choice machine is not available.
### 6. Tutorial Notebook

There's a Jupyter notebook [Fusion_tutorial_example.ipynb](Fusion_tutorial_example.ipynb) that runs a simplified flow and breaks down how to deploy it with explanations.
