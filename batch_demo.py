from globus_automate_client import create_flows_client
from start_fusion_flow import run_flow, endpoint_active,set_flow_input
import time, uuid
import argparse
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="./fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")

def arg_parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('--nbatch', default=4, help=f'Number of runs')
    parser.add_argument('--wait-time', default=0, help=f'Wait time in seconds between runs')
    parser.add_argument('--label', default="fusion-batch-test", help=f'Batch label')
    parser.add_argument('--machine', default="polaris", help=f'Machine to run at')
    parser.add_argument('--dynamic', default=False, action='store_true', help=f'Dynamically choose available machine')
    parser.add_argument('--rand-iter', default=10, help=f'Randomly, for every 1 out of rand-iter runs switch machines')

    return parser.parse_args()


if __name__ == '__main__':

    args = arg_parse()

    nruns = int(args.nbatch)
    injection_wait_time = int(args.wait_time)
    tags = ['batch_test']
    json_input_path = "./input.json"
    label_base = args.label
    machine = args.machine
    dynamic = args.dynamic
    rand_iter = args.rand_iter
    if rand_iter != None:
        rand_iter = float(rand_iter)


    flow_input = set_flow_input(machine, json_input_path, None, None, None)

    test_tag = uuid.uuid4()
    tags.append(str(test_tag))
    print(f"--------------------------------")
    print(f"DIII-D to ALCF NEXUS Demo SC2023")
    print(f"Launching {nruns} runs with a {injection_wait_time}s wait time between each")
    #print(f"injection_time: {injection_wait_time} s")
    #print(f"label: {label_base}")
    print(f"test_series_tag_id: {test_tag}")
    print(f"--------------------------------")

    endpoint_status = endpoint_active(flow_input["input"]["compute_endpoint_id"])
    #print(endpoint_status)

    #if endpoint_status:

    fc = create_flows_client()
    flow = fc.get_flow(flow_id)
    flow_scope = flow['globus_auth_scope']

    run_ids = []
    start_times = []
    run_machines = []
    nruns_created = 0
    nruns_returned = 0
    last_run_time = time.time()-injection_wait_time
    
    while nruns_created < nruns or nruns_returned < nruns:
        #for i in range(nruns):
        if nruns_created < nruns and time.time()-last_run_time > injection_wait_time:
            i = nruns_created
            rand_iter_i = rand_iter
            if i == 0:
                rand_iter_i = None
            label = label_base+f"-{i+1}/{nruns}"
            source_path = "/home/simpsonc/fusion"
            destination_relpath = f"test_runs/batch_test/{test_tag}/{i}"
            return_path = f"/home/simpsonc/fusion_return/{test_tag}/{i}"
            run,run_machine = run_flow(json_input_path, 
                            source_path, 
                            None, 
                            return_path, 
                            dynamic=dynamic,
                            destination_relpath=destination_relpath, 
                            machine=machine, label=label, tags=tags, 
                            flow_client=fc,
                            random_machine_iter=rand_iter_i)
            start_times.append(time.time())
            print(f"Starting {label}")
            run_ids.append(run["run_id"])
            run_machines.append(run_machine)
            nruns_created += 1
            last_run_time = time.time()

        #nruns_returned = nruns

        if "polaris" not in run_machines:
            nperlmutter = sum([1 for m in run_machines if m == "perlmutter"])
            nsummit = sum([1 for m in run_machines if m == "summit"])
            if nperlmutter > 0:
                print(f"Perlmutter has {nperlmutter} remaining run(s)")
            if nsummit > 0:
                print(f"Summit has {nsummit} remaining run(s)")
            print("We won't wait for alternate site run(s) in this demo")
            break

        for i,run_id in enumerate(run_ids):
            run_state = fc.flow_action_status(flow_id, flow_scope, run_id)
            end_time = time.time()
            status = run_state["status"]
            label = run_state["label"]
            
            if status in ["SUCCEEDED", "FAILED"] :
                start_time = start_times[i]
                print(f"Run {label}: {status} after {round(end_time-start_time)}s on {run_machines[i]}")
                nruns_returned += 1
                run_ids.pop(i)
                start_times.pop(i)
                run_machines.pop(i)
        
        
