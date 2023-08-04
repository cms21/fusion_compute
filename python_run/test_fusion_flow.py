from globus_automate_client import create_flows_client

from dotenv import load_dotenv
import os, json, time, uuid

from start_fusion_compute import run_flow
from start_fusion_compute import endpoint_active

load_dotenv(dotenv_path="../fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")


if __name__ == '__main__':

    nruns = 3
    injection_wait_time = 1
    tags = []
    monitor = True
    flow_input = json.load(open("../input.json"))
    label = f"fusion-run"

    flow_input["input"]["recursive_tx"] = False # set false to copy a file, true for a directory
    flow_input['input']['source']['path'] = "/csimpson/polaris/fusion/dummy.txt"
    flow_input['input']['destination']['path'] = "/datascience/csimpson/fusion/dummy_data/dummy.txt"

    test_tag = uuid.uuid4()
    tags.append(str(test_tag))

    print(f'''nruns: {nruns}
injection_time: {injection_wait_time} s
label: {label}
test_series_tag_id: {test_tag}''')

    if endpoint_active(flow_input):
        
        fc = create_flows_client()
        flow_actions = []
        for i in range(nruns):
            flow_input['input']['destination']['path'] = f"/datascience/csimpson/fusion/dummy_data/dummy_{i}.txt"
            flow_action = run_flow(flow_input,
                                   label=label+f"-{i+1}/{nruns}",
                                   flow_client=fc,
                                   tags=tags)
            flow_actions.append(flow_action)

            time.sleep(injection_wait_time)

        if monitor:
            print("Monitoring...")
            for flow_action in flow_actions:
                
                flow_action_id = flow_action['action_id']
                flow_status = flow_action['status']

                while flow_status == 'ACTIVE':
                    time.sleep(10)
                    flow_action = fc.flow_action_status(flow_id, None, flow_action_id)
                    flow_status = flow_action['status']
                    print(f'Flow status: {flow_status}')
