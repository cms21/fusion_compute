# fusion_compute
Scripts to deploy fusion application on ALCF systems with Globus Flows

## Setup on Polaris
First login to Polaris and do the following things:
### 1. Create an environment and install necessary packages
```
module load conda
conda create fusion_flow
conda activate fusion_flow
pip install globus_automate_client globus_compute_sdk
```
### 2. Create a Globus Endpoint
You need to choose a target queue for your workflow.  Use the provided `endpoint_config` as a model (replace your project name etc.)

Copy the endpoint ID for the next step.

## Setup on Iris
### 1. Clone this repo
Paste the enpoint ID into `fusion.env_template` and copy it to `fusion.env`.

```
cp fusion.env_template fusion.env
```
### 1.1 Make an environment and install globus
### 2. Run the setup script
```
python setup_fusion_flow.py
```

This should create a new file `input.json` and modify `fusion.env` by adding some new environment variables
### 3. Run the flow
There are two ways to start the flow.
### 3a. CLI
Start the flow by typing at the command line:
```
globus flows start --input input.json ${GLOBUS_FLOW_ID}
```
### 3b. Python
Alternatively, you can start the flow using the python script:
```
python start_fusion_compute.py
```

Both of these approaches will transfer a file and run the fusion application once.  To run this sequence of actions repeatedly, you can call the CLI command from a bash script in a loop or call the python call from a python script in a loop.
