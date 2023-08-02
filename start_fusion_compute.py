from globus_automate_client import create_flows_client
import globus_compute_sdk
from dotenv import load_dotenv
import os, json, time, uuid
from datetime import datetime

load_dotenv(dotenv_path="./fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")

def endpoint_active(flow_input):
    gc = globus_compute_sdk.Client()
    endpoint_id = flow_input["input"]["compute_endpoint_id"]
    endpoint_status = gc.get_endpoint_status(endpoint_id)['status']
    endpoint_metadata = gc.get_endpoint_metadata(endpoint_id)
    if endpoint_status != 'online':
        print(f"Endpoint {endpoint_metadata['name']} is {endpoint_status}")
        print(f"Login into {endpoint_metadata['hostname']} and restart endpoint")
        return False
    else:
        return True

def test_multiflow(flow_input, monitor=False,label=None, nruns=1,tags=None):

    test_tag = uuid.uuid4()
    if tags is None: tags = []
    tags.append(str(test_tag))

    if endpoint_active(flow_input):
        
        fc = create_flows_client()
        flow_actions = []
        for i in range(nruns):
            flow_action = run_flow(flow_input,
                                   label=label+f"-{i+1}/{nruns}",
                                   flow_client=fc,
                                   tags=tags)
            flow_actions.append(flow_action)

        if monitor:
            for flow_action in flow_actions:
                print(flow_action)
                flow_action_id = flow_action['action_id']
                flow_status = flow_action['status']
                print(f'Flow action started with id: {flow_action_id}')

                while flow_status == 'ACTIVE':
                    time.sleep(10)
                    flow_action = fc.flow_action_status(flow_id, None, flow_action_id)
                    flow_status = flow_action['status']
                    print(f'Flow status: {flow_status}')
        return True
    else:
        return False
    
def run_flow(flow_input,label=None, tags=None, flow_client=None):

    if endpoint_active(flow_input):
        if flow_client is None:
            flow_client = create_flows_client()
        flow = flow_client.get_flow(flow_id)
        flow_scope = flow['globus_auth_scope']
        flow_action = flow_client.run_flow(flow_id, flow_scope, flow_input, label=label, tags=tags)        
        return flow_action
    else:
        return None


if __name__ == '__main__':

    nruns = 3
    flow_input = json.load(open("./input.json"))
    label = f"fusion-run"
    test_multiflow(flow_input, monitor=False, label=label, nruns=nruns)