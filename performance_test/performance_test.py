from fusion_compute import ENV_PATH
from fusion_compute.utils import get_flows_client
from fusion_compute.machine_settings import machine_settings
from fusion_compute.start_fusion_flow import run_flow
import globus_compute_sdk
from globus_compute_sdk.serialize import CombinedCode
from globus_sdk.services.flows.errors import FlowsAPIError
from dotenv import load_dotenv
import os
import time
import shortuuid
import numpy as np
import argparse

load_dotenv(dotenv_path=ENV_PATH)
client_id = os.getenv("CLIENT_ID")
flow_id = os.getenv("GLOBUS_FLOW_ID")

fc = get_flows_client(client_id=client_id)

def make_delay_test(inputs_batch,
                         machines=["polaris"],
                         niter=1,
                         delay=0,
                         filename="perf_test",):

    test_label = shortuuid.ShortUUID().random(length=8)

    runs = []

    for machine in machines:
        for n in inputs_batch.keys():
            inputs_function_kwargs = inputs_batch[n]
            for i in range(niter):
                runs.append(run_flow(source_path=f'/home/simpsonc/fusion/perf_test/{machine}/{n}/{i}',
                                    return_path=f'/home/simpsonc/fusion_return/perf_test/{machine}/{n}/{i}',
                                    machine=machine,
                                    inputs_function_kwargs=inputs_function_kwargs,
                                    destination_relpath=f"test_runs/perf_test/{n}/{i}",
                                    label=f"{test_label}_{n}_{i}"))
                time.sleep(delay)

    print(f"Started {len(runs)} runs for test {test_label}")
    np.save(filename+"_"+test_label,runs)

    return runs

def get_runs_status(batch_runs,batch_status):

    for ir in range(len(batch_runs)):
        try:
            retry_attempt = 0
            if batch_status[ir] in ["ACTIVE","INACTIVE"]:
                batch_status[ir] = fc.get_run(batch_runs[ir])["status"]
        except FlowsAPIError as e:
            if "Too Many Requests" in e and retry_attempt < 10:
                not_updated = True
                while retry_attempt < 10 and not_updated:
                    retry_attempt += 1
                    time.sleep(2**retry_attempt)
                    try:
                        print(f"Retrying status query ({retry_attempt}/10)")
                        batch_status[ir] = fc.get_run(batch_runs[ir])["status"]
                        not_updated = False
                    except FlowsAPIError as e:
                        continue
                if not_updated:
                    raise FlowsAPIError(e)
                else:
                    continue
            else:
                raise FlowsAPIError(e)
    return batch_status


def run_and_wait_for_workers(inputs_batch, 
                             machine="polaris",
                             niter_per_instance=1,
                             test_label="perf_test",
                             pause_interval = 10,
                             retry_failed=True,
                             failed_niter=None):

    n_workers = get_endpoint_workers(machine=machine,verbose=True)
    inputs_keys = [k for k in inputs_batch.keys()]
    
    batch_status = []
    batch_runs = []
    batch_kwargs = []
    batch_input_keys = []
    n_created = 0

    nruns = len(inputs_batch)*niter_per_instance
    if failed_niter is not None:
        nruns = sum([failed_niter[k] for k in failed_inputs_niter.keys()])
    
    for run in range(len(inputs_batch)):

        # Get inputs for run   
        input_key = inputs_keys[run]
        inputs_function_kwargs = inputs_batch[input_key]
        
        niter = niter_per_instance
        if failed_niter is not None:
            niter = failed_niter[input_key]

        # Create the specified number of run iterations
        for iter in range(niter):

            run_id = run_flow(source_path=f'/home/simpsonc/fusion/{test_label}/{machine}/{input_key}/{iter}',
                    return_path=f'/home/simpsonc/fusion_return/{test_label}/{machine}/{input_key}/{iter}',
                    destination_relpath=f"test_runs/{test_label}/{input_key}/{iter}",
                    machine=machine,
                    inputs_function_kwargs=inputs_function_kwargs,
                    label=f"{test_label}_{input_key}_{iter}",
                    )

            batch_input_keys.append(input_key)
            batch_kwargs.append(inputs_function_kwargs)
            batch_runs.append(run_id)
            batch_status.append(fc.get_run(run_id)["status"])
            n_created += 1
            n_running = len([status for status in batch_status if status in ["ACTIVE","INACTIVE"]])

            # Pause if all workers are running flows or if we are waiting for last run to complete
            while (n_running == min(n_workers,nruns)) or (n_created == nruns and ("ACTIVE" in batch_status or "INACTIVE" in batch_status)):
                time.sleep(pause_interval)
                batch_status = get_runs_status(batch_runs,batch_status)
                n_running = len([status for status in batch_status if status in ["ACTIVE","INACTIVE"]])
                #n_workers = get_endpoint_workers(machine=machine,verbose=True)
                report_status,status_count = np.unique(batch_status,return_counts=True)
                status_string = "status: "
                for rs,sc in zip(report_status,status_count):
                    status_string+=f"{sc} run(s) {rs}, "
                status_string += f"{n_workers} workers"
                print(status_string)            

    # Report final status
    n_failed = 0                           
    report_status,status_count = np.unique(batch_status,return_counts=True)
    status_string = "final status: "
    for rs,sc in zip(report_status,status_count):
        status_string+=f"{sc} run(s) {rs} "
        if sc == "FAILED":
            n_failed = rs
    print(status_string)

    # Retry failed runs, if required
    if retry_failed and n_failed > 0:
        retry_batch_runs = retry_failed_runs(batch_runs,batch_status,batch_input_keys,batch_kwargs,
                                            machine,test_label,retry_failed)
        batch_runs += retry_batch_runs

    return batch_runs

def retry_failed_runs(batch_runs,batch_status,batch_input_keys,batch_kwargs,
                      machine,test_label,retry_failed):
    failed_inputs_batch = {}
    failed_inputs_niter = {}

    for ir in range(len(batch_runs)):
        run_info = fc.get_run(batch_runs[ir])
        status = run_info["status"]
        batch_status[ir] = status
        if status == 'FAILED':
            cause = run_info["details"]["details"]["cause"]["details"]["result"][0]
            # If the cause of the failure was an interrupted function due a batch job ending, set it up to be restarted on next pass
            # The exception in this case will be 'ManagerLost'
            if "ManagerLost" in cause:
                if batch_input_keys[ir] in failed_inputs_batch.keys():
                    failed_inputs_niter[batch_input_keys[ir]] += 1
                else:
                    failed_inputs_batch[batch_input_keys[ir]] = batch_kwargs[ir]
                    failed_inputs_niter[batch_input_keys[ir]] = 1

    print(f"Retrying {sum([failed_inputs_niter[k] for k in failed_inputs_niter.keys()])} runs")
    retry_batch_runs = run_and_wait_for_workers(failed_inputs_batch,
                                                machine=machine,
                                                test_label=test_label,
                                                retry_failed=retry_failed,
                                                failed_niter=failed_inputs_niter)
    return retry_batch_runs


def activate_endpoint(machine="polaris"):

    def hello_world():
        import os
        return f"Hello CUDA device {os.getenv('CUDA_VISIBLE_DEVICES')}, hello OMP {os.getenv('OMP_NUM_THREADS')}"
    
    settings = machine_settings()[machine]
    gcc = globus_compute_sdk.Client(code_serialization_strategy=CombinedCode())
    gce = globus_compute_sdk.Executor(endpoint_id=settings["compute_endpoint"],client=gcc)
    future = gce.submit(hello_world)
    print(future.result())
    return

def get_endpoint_workers(machine="polaris",
                         verbose=False):
    settings = machine_settings()[machine]
    compute_endpoint_id = settings["compute_endpoint"]
    gc = globus_compute_sdk.Client()
    n_workers = 0
    retries = 0
    while n_workers == 0 and retries < 10:
        time.sleep(2**retries)
        endpoint_status = gc.get_endpoint_status(compute_endpoint_id)
        n_workers = int(endpoint_status["details"]["total_workers"])
        retries += 1
        if verbose:
            print(f"Querying workers: found {n_workers} after {retries} tries")
    if n_workers == 0:
        print("No workers found after max tries, activate endpoint")
        activate_endpoint(machine=machine)
        time.sleep(30)
        endpoint_status = gc.get_endpoint_status(compute_endpoint_id)
        n_workers = int(endpoint_status["details"]["total_workers"])
        if n_workers == 0:
            raise Exception("No workers found")
    return n_workers

def make_sequential_test(inputs_batch, 
                         machines=["polaris","perlmutter"],
                         niter=1):

    test_label = "test_"+shortuuid.ShortUUID().random(length=8)
    print(f"Begun sequential test {test_label}")

    for machine in machines:
       
        activate_endpoint(machine=machine)
        
        batch_runs = run_and_wait_for_workers(inputs_batch,
                                        machine=machine, 
                                        niter_per_instance=niter,
                                        test_label=test_label)
            
    file_name = f'sequential_test_{test_label}'
    np.save(file_name,batch_runs)
    print(f"saved file {file_name}")
    
    return batch_runs


def assemble_ionorb_input_kwargs(testfile=None, 
                          shot=[164869], 
                          stime=[3005], 
                          efitnum=["EFIT01"], 
                          profdata=[1], 
                          beam_num=[1], 
                          energykev=["FULL"], 
                          nparts=[1000],):
    return_kwargs = {}
    if testfile == None:
        return_kwargs_list = _assemble_kwargs( 
                            shot=shot, 
                            stime=stime, 
                            efitnum=efitnum, 
                            profdata=profdata, 
                            beam_num=beam_num, 
                            energykev=energykev, 
                            nparts=nparts,)
    else:
        print(f"Read inputs from file")
        return_kwargs_list = []
        with open(testfile,"r") as f:
            #shots,time0s,time1s,steps = np.genfromtxt(f,unpack=True,dtype=int)
            lines = f.readlines()
            #for shot,time0,time1,step in zip(shots,time0s,time1s,steps):
            for line in lines:
                if line[0] == "#":
                    continue
                shot,time0,time1,step = line.split()
                time = int(time0)
                time1 = int(time1)
                step = int(step)
                stimes = []
                while time <= time1:
                    stimes.append(time)
                    time += step
                shot_kwargs_list = _assemble_kwargs(shot=[shot],
                                            stime=stimes,
                                            efitnum=efitnum,
                                            profdata=profdata,
                                            beam_num=beam_num,
                                            energykev=energykev,
                                            nparts=nparts)
                return_kwargs_list += shot_kwargs_list
            
    nkwargs = len(return_kwargs_list)
    for n in range(nkwargs):
        return_kwargs[str(n)] = return_kwargs_list[n]
    return return_kwargs

def _assemble_kwargs(**kwargs):
    
    return_kwargs = []
 
    nruns = 1
    for key in kwargs:
        nruns *= len(kwargs[key])
    print(f"Assembling kwargs for {nruns} sets of inputs")

    for n in range(nruns):
       return_kwargs.append({})

    for key in kwargs:
        iv = 0
        nvals = len(kwargs[key])
        for n in range(nruns):
            v = kwargs[key][iv]
            iv = min(iv+1,nvals-1)
            return_kwargs[n][key] = v    
        
    return return_kwargs


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--machine', default='polaris', help=f'Target machine for flow', choices=machine_settings().keys())
    
    return parser.parse_args()


if __name__ == '__main__':

    args = arg_parse()

    inputs = assemble_ionorb_input_kwargs(nparts=[1000,10000])
    make_sequential_test(inputs, machines=["polaris"],niter=4)
