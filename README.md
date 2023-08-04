# fusion_compute
Scripts to deploy fusion application on ALCF systems with Globus Flows

## Setup on Polaris
First login to Polaris and do the following things:
### 1. Create an environment and install necessary packages
```
module load conda
conda create -n fusion python==3.9
conda activate fusion
pip install globus-compute-endpoint
pip install globus-automate-client
```
### 2. Create a Globus Endpoint
Use the provided `config.yml_template` as a model to configure your endpoint. Edit it to replace your project name, environment name, etc.  Then do:

```
globus-compute-endpoint configure --endpoint-config config.yml_template <YOUR_ENDPOINT_NAME>
globus-compute-endpoint start <YOUR_ENDPOINT_NAME>
globus-compute-endpoint list
```

Copy the endpoint ID for the next step.

## Setup on Iris
### 1. Clone this repo
Paste the enpoint ID into `fusion.env_template` and copy it to `fusion.env`.

```
cp fusion.env_template fusion.env
```
### 1.1 Make an environment and install globus

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

### 2. Run the setup script
```
python setup_fusion_flow.py
```

When running this script for the first time, you may be asked to authenticate your ALCF credentials with globus two times.  Running this script should create a new file `input.json` and modify `fusion.env` by adding some new environment variables containing the IDs of the flow and function.

Login to globus.  You will be directed to a web page to validate your globus credentials.
```
globus login
```

### 3. Run the flow
There are two ways to start the flow.
### 3a. CLI
Validate your credentials to use the flow we have created (you will only have to do this once):
```
export $(cat fusion.env | xargs)
globus login --flow ${GLOBUS_FLOW_ID}
```
Start the flow by typing at the command line:
```
globus flows start --input input.json ${GLOBUS_FLOW_ID}
```
### 3b. Python
Alternatively, you can start the flow using the python script:
```
python start_fusion_compute.py
```
You will be prompted to validate your globus credentials the first time you run this script.

Both of these approaches will transfer a file and run the fusion application once.  To run this sequence of actions repeatedly, you can call the CLI command from a bash script in a loop or call the python call from a python script in a loop.
