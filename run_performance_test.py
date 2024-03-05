from dotenv import load_dotenv
import globus_compute_sdk
from utils import get_flows_client, get_specific_flow_client
#from functions import hello_world
from start_fusion_flow import machine_settings
from start_fusion_flow import run_flow
import os, time
from dateutil.parser import parse
from matplotlib import pyplot as plt
import random
import numpy as np
import datetime


load_dotenv(dotenv_path="./fusion.env")
client_id = os.getenv("CLIENT_ID")
flow_id = os.getenv("GLOBUS_FLOW_ID")


fc = get_flows_client(client_id=client_id)


#run_id = "97fcb172-e115-4552-b40c-7ad558ccd83d"

def run_performance_test(machines=["polaris"],
                         niter=1,
                         nparts_test=[10000],
                         filename="run_test"):
    
    runs = []

    for machine in machines:
        activate_endpoint(machine=machine)
        for nparts in nparts_test:
            for n in range(niter):
                runs.append(run_perf_instance(machine=machine,
                                              inputs_function_kwargs={"nparts": nparts},
                                              source_path=f'/home/simpsonc/fusion/perf_test/{machine}/{nparts}/{n}',
                                              destination_relpath=f"test_runs/perf_test/{nparts}/{n}",
                                              return_path=f'/home/simpsonc/fusion_return/perf_test/{machine}/{nparts}/{n}'))

    np.save(filename,runs)

    return runs


def run_perf_instance(machine="polaris",
                      inputs_function_kwargs={},
                      source_path='/home/simpsonc/fusion/perf_test',
                      destination_relpath="test_runs/perf_test",
                      return_path='/home/simpsonc/fusion_return/'):
    
    settings = machine_settings[machine]
    
    run_id = run_flow(input_json="./input.json",
                    source_path=source_path,
                    destination_path=f'{settings["scratch_path"]}/test_runs/test/',
                    return_path=return_path,
                    destination_relpath=destination_relpath,
                    machine=machine,
                    inputs_function_kwargs=inputs_function_kwargs,
                    )
    return run_id

def wait_perf_instance(machine="polaris",inputs_function_kwargs={"nparts":1000},niter=1,n_workers=4):

    n_workers = get_endpoint_workers(machine=machine)

    batch_status = []
    batch_runs = []
    n = inputs_function_kwargs["nparts"]
    #for iw in range(n_workers):

    n_created = 0
    for i in range(niter):
        
        #for i in range(niter):
        #for iw in range(n_workers):
        run_id = run_perf_instance(machine=machine,
                                inputs_function_kwargs=inputs_function_kwargs,
                                source_path=f'/home/simpsonc/fusion/perf_test/{machine}/{n}/{i}',
                                return_path=f'/home/simpsonc/fusion_return/perf_test/{machine}/{n}/{i}',
                                destination_relpath=f"test_runs/perf_test_batch/{n}/{i}"
                                )
        batch_runs.append(run_id)
        batch_status.append(fc.get_run(run_id)["status"])
        n_created += 1
        #time.sleep(1)

        #status = fc.get_run(run_id)["status"]
        #while status not in ["SUCCEEDED","FAILED"]:
        if n_created == n_workers:
            while "ACTIVE" in batch_status or "INACTIVE" in batch_status:
                print(f"status {batch_status}")
                time.sleep(10)
                #status = fc.get_run(run_id)["status"]

                for i in range(len(batch_runs)):
                    batch_status[i] = fc.get_run(batch_runs[i])["status"]
            n_created = 0

        print(f"status {batch_status}")
    
    return batch_runs

def activate_endpoint(machine="polaris"):

    def hello_world():
        import os
        return f"Hello CUDA device {os.getenv('CUDA_VISIBLE_DEVICES')}, hello OMP {os.getenv('OMP_NUM_THREADS')}"

    settings = machine_settings[machine]
    gce = globus_compute_sdk.Executor(endpoint_id=settings["compute_endpoint"])
    future = gce.submit(hello_world)
    print(future.result())
    return

def get_endpoint_workers(machine="polaris"):
    settings = machine_settings[machine]
    compute_endpoint_id = settings["compute_endpoint"]
    gc = globus_compute_sdk.Client()
    endpoint_status = gc.get_endpoint_status(compute_endpoint_id)
    n_workers = int(endpoint_status["details"]["total_workers"])
    return n_workers

def make_sequential_test(machines=["polaris","perlmutter"], particle_counts=[1000,10000,100000,1000000],niter=1):
    print("Begun sequential test")
    
    for machine in machines:
       
        # This will start the compute endpoint of the target machine
        activate_endpoint(machine=machine)
        for n in particle_counts:
            batch_runs = wait_perf_instance(machine=machine, inputs_function_kwargs={"nparts":n},niter=niter)

            
    file_name = f'perf_batch_test_sequential_{datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")}'
    np.save(file_name,batch_runs)
    print(f"saved file {file_name}")
    
    return batch_runs

