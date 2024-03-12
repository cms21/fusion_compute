from dotenv import load_dotenv
from fusion_compute import ENV_PATH
import globus_compute_sdk
from fusion_compute.utils import get_flows_client
#from functions import hello_world
from fusion_compute.machine_settings import machine_settings
from fusion_compute.start_fusion_flow import run_flow
from globus_compute_sdk.serialize import CombinedCode
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
        activate_endpoint(machine=machine)
        for n in inputs_batch.keys():
            inputs_function_kwargs = inputs_batch[n]
            for i in range(niter):
                runs.append(run_perf_instance(machine=machine,
                                              inputs_function_kwargs=inputs_function_kwargs,
                                              source_path=f'/home/simpsonc/fusion/perf_test/{machine}/{n}/{i}',
                                              destination_relpath=f"test_runs/perf_test/{n}/{i}",
                                              return_path=f'/home/simpsonc/fusion_return/perf_test/{machine}/{n}/{i}',
                                              test_label=f"{test_label}_{n}_{i}"))
                time.sleep(delay)

    np.save(filename+"_"+test_label,runs)

    return runs


def run_perf_instance(machine="polaris",
                      inputs_function_kwargs={},
                      source_path='/home/simpsonc/fusion/perf_test',
                      destination_relpath="test_runs/perf_test",
                      return_path='/home/simpsonc/fusion_return/',
                      test_label="perf_test"):
    
    run_id = run_flow(source_path=source_path,
                    return_path=return_path,
                    destination_relpath=destination_relpath,
                    machine=machine,
                    inputs_function_kwargs=inputs_function_kwargs,
                    label=test_label
                    )
    return run_id

def run_and_wait_for_workers(inputs_batch, 
                             machine="polaris",
                             niter_per_instance=1,
                             test_label="perf_test",
                             retry_failed=False):

    n_workers = get_endpoint_workers(machine=machine)
    inputs_keys = [k for k in inputs_batch.keys()]
    
    batch_status = []
    batch_runs = []
    
    instance = 0
    # Total number of runs
    nruns = len(inputs_batch)*niter_per_instance
    for i in range(nruns):
        # Get inputs for instance
        if i%niter_per_instance == 0:
            input_key = inputs_keys[instance]
            inputs_function_kwargs = inputs_batch[input_key]
            instance += 1
        

        run_id = run_perf_instance(machine=machine,
                                inputs_function_kwargs=inputs_function_kwargs,
                                source_path=f'/home/simpsonc/fusion/{test_label}/{machine}/{input_key}/{i}',
                                return_path=f'/home/simpsonc/fusion_return/{test_label}/{machine}/{input_key}/{i}',
                                destination_relpath=f"test_runs/{test_label}/{input_key}/{i}",
                                test_label=f"{test_label}_{input_key}_{i}"
                                )
        batch_runs.append(run_id)
        batch_status.append(fc.get_run(run_id)["status"])
        n_created += 1
        
        n_running = len([status for status in batch_status if status in ["ACTIVE","INACTIVE"]])
    
        # Pause if all workers are running flows or if we are on the last run and are waiting for remaining runs to complete
        while (n_running == min(n_workers,nruns)) or (i == nruns-1 and ("ACTIVE" in batch_status or "INACTIVE" in batch_status)):

            n_workers = get_endpoint_workers(machine=machine)
            report_status,status_count = np.unique(batch_status,return_counts=True)
            status_string = "status: "
            for rs,sc in zip(report_status,status_count):
                status_string+=f"{sc} run(s) {rs}, "
            status_string += f"{n_workers} workers"
            time.sleep(10)

            for i in range(len(batch_runs)):
                batch_status[i] = fc.get_run(batch_runs[i])["status"]
            n_running = len([status for status in batch_status if status in ["ACTIVE","INACTIVE"]])
        

    report_status,status_count = np.unique(batch_status,return_counts=True)
    status_string = "final status: "
    for rs,sc in zip(report_status,status_count):
        status_string+=f"{sc} run(s) {rs} "
        if rs == "FAILED":
            n_failed = sc
    
    # if retry_failed and n_failed > 0:
    #     print(f"Retrying {n_failed} runs")
    #     for run_id,status in zip(batch_runs,batch_status):
    #         if status == "FAILED":
    #             run_info = fc.get_run(run_id)

    #     wait_perf_instance(inputs_function_kwargs, machine=machine,input_batch=input_batch,niter=n_failed,test_label=test_label)
    
    
    return batch_runs

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

def get_endpoint_workers(machine="polaris",max_wait = 300):
    settings = machine_settings()[machine]
    compute_endpoint_id = settings["compute_endpoint"]
    gc = globus_compute_sdk.Client()
    n_workers = 0
    time_elapsed = 0
    start_time = time.time()
    while n_workers == 0 and time_elapsed < max_wait:
        endpoint_status = gc.get_endpoint_status(compute_endpoint_id)
        n_workers = int(endpoint_status["details"]["total_workers"])
        time_elapsed = time.time() - start_time
    if n_workers > 0:
        return n_workers
    else:
        raise Exception

def make_sequential_test(inputs_batch, machines=["polaris","perlmutter"],niter=1):

    test_label = "test_"+shortuuid.ShortUUID().random(length=8)
    print(f"Begun sequential test {test_label}")

    for machine in machines:
       
        # This will start the compute endpoint of the target machine
        activate_endpoint(machine=machine)
        
        #for k in inputs_batch.keys():
        #    inputs_function_kwargs = inputs_batch[k]
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

    inputs = assemble_ionorb_input_kwargs(nparts=[10000])
    make_sequential_test(inputs, machines=["polaris"],niter=16)
