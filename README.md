# fusion_compute

This repository contains scripts to deploy the Ionorb workflow for DIII-D on machines at ALCF and NERSC.  This implementation uses Globus Flows.  It requires the user to setup the various Globus transfer and compute endpoints under the user's account.  Future work will make use of a DIII-D institutional transfer endpoint and compute endpoints run by service and robot accounts at ALCF and NERSC.  There is also planned development to create inputs using Toksys and FORTRAN code.

This repositiory will allow a user to trigger a Globus flow that will run Ionorb on Polaris or Perlmutter from the user's local machine.  The steps that each flow run does are:

#### 1. Create input files for Ionorb on the machine Omega at DIII-D
#### 2. Transfer input files to either Polaris or Perlmutter
#### 3. Run Ionorb on Polaris or Perlmutter (depending on where the input data were sent)
#### 4. Run a postprocessing analysis script that uses the outputs of Ionorb to compute the peak power deposited on the DIII-D inner wall
#### 5. Transfer Ionorb results back to Omega at DIII-D

## 1. Get a Globus Client ID

You can create a new Client ID by going to [developers.globus.org](developers.globus.org).  Click on "Register a thick client or script that will be installed and run by users on their devices".

If you'd like to skip this step, email Christine at csimpson@anl.gov and she can share a client id for you to use.

## 2. Setup on Omega at DIII-D

Login to Omega.

### 0. Create Globus Transfer endpoint
NOTE!!! Once DIII-D has installed its planned institutional Globus transfer endpoint, the user should use that endpoint and skip this step.

Create a Globus connect personal transfer endpoint.  Follow instructions [here](https://docs.globus.org/globus-connect-personal/install/linux/).  Start the transfer endpoint and copy the transfer endpoint ID.

### 1. Load the globus module and create a Globus Compute endpoint

First clone this repo:

```bash
git clone git@github.com:cms21/fusion_compute.git
```

Load the globus module and configure the compute endpoint:

```bash
module load globus
cd fusion_compute/endpoint_configs
globus-compute-endpoint configure --endpoint-config omega_short_config.yaml omega_short
globus-compute-endpoint start omega_short
globus-compute-endpoint list
```
Copy the compute endpoint ID.

## 3. Setup on Polaris

Login to Polaris.

First clone this repo:

```bash
git clone git@github.com:cms21/fusion_compute.git
```

Load the globus module and configure the compute endpoint:

```bash
module load conda
conda activate /eagle/IRIBeta/fusion/fusion_env
cd fusion_compute/endpoint_configs
globus-compute-endpoint configure --endpoint-config polaris_config_template.yaml polaris
globus-compute-endpoint start polaris
globus-compute-endpoint list
```

Copy the compute endpoint ID.

## 4. Setup on Perlmutter


## 5. Setup on Local Machine

### 1. First clone this repo:

```bash
git clone git@github.com:cms21/fusion_compute.git
```

### 2. Install

Create a conda module or a python virtual environment.  Install this package and its dependencies.

```bash
cd fusion_compute
pip install -e .
```

### 3. Copy fusion.env_template to fusion.env

```bash
cp fusion.env_template fusion.env
```
Edit `fusion.env`.  Paste in your compute endpoint ids.

### 4. Machine settings

In [machine_settings.py](fusion_compute/machine_settings.py), edit any necessary paths on the machines you are using.

### 5. Test functions.

Test the functions used in the workflow.  First, test on Omega:

```bash
cd fusion_compute
python functions.py --test --machine omega
```

Then, test on Polaris/Perlmutter:
```bash
cd fusion_compute
python functions.py --test --machine polaris
```

You may be prompted to validate your credentials with Globus if this is your first time running a Globus Compute function. 

Note that these tests will appear to hang while your job is queued on the machine scheduler.  For this first test, check to see if your job has been created.

### 6. Register your functions

```bash
cd fusion_compute
python functions.py
```

You should see the function ids appear in fusion.env.

### 7. Set up the flow and establish authentication with the Globus Service.

```bash
cd fusion_compute
python register_flow.py
```

You should be prompted to establish your credentials with the Globus service twice.

You should see the Flow id appear in fusion.env.

### 8. Test the flow.

```bash
cd fusion_compute
python start_fusion_flow.py --source_path <SRC_PATH> --destination_path <DEST_PATH> --return_path <RET_PATH>
```
`<SRC_PATH>` and `<RET_PATH>` are paths on Omega (where the input files are created and where results are returned at the end of the flow).

`<DEST_PATH>` is a path on Polaris or Perlmutter.


## Trigger Script

There's a trigger bash script that wraps around `start_fusion_flow.py`, [d3d_trigger.sh](d3d_trigger.sh).  This could be used to bundle the flow with the local execution of IDL scripts.

You can run the trigger script like this
```bash
d3d_trigger.sh --machine <MACHINE> --dynamic
```
If you include the --machine option, the flow will attempt to run on that machine.  If it is not included, it will try to run on Polaris.  If `--dynamic` is included, the agent will adapt to run on a different machine if the first-choice machine is not available.

## Performance test

There are two performance test runners `make_delay_test()` and `make_sequential_test()`.

`make_delay_test()` will take a batch of test flows and run 1 flow every `delay` time, where `delay` is a time specified in seconds.

`make_sequential_test()` will detect the number of active workers on Polaris/Perlmutter and only create enough active flows to fill those workers.  This test runner should be used when testing action performance.  In this test, the Ionorb action will begin immediately and therefore will not include wait time from the machine scheduler or the globus compute interchange.

To run a sequential test:
```python
from performance_test import make_sequential_test
from performance_test import assemble_ionorb_input_kwargs

inputs = assemble_ionorb_input_kwargs(nparts=[1000,10000,100000])

make_sequential_test(inputs, machines=["polaris"],niter=16)
```
This will run the test slice 16 times for 3 different particle numbers, 1000, 10,000 and 100,000 particles.

To run slices from a file:
```python
from performance_test import make_sequential_test
from performance_test import assemble_ionorb_input_kwargs

inputs = assemble_ionorb_input_kwargs(testfile="collection_of_multi-slice_shots.txt",
                                          nparts=[50000])
make_sequential_test(inputs, machines=["polaris"],niter=1)
```
This will run a 50,000 particle test for every slice contained in the `testfile` one time.

An 8 character random string will be assigned to each sequential test.  This string can be used to query the runs of the test.

## Performance plots

To create performance plots of a test, use the `test_label`.

For example:
```bash
python plot_performance.py --test-label DHtaGbRZ
```
