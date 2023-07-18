from globus_automate_client import create_flows_client
from dotenv import load_dotenv
import os, json

load_dotenv(dotenv_path="./fusion.env")
flow_id = os.getenv("GLOBUS_FLOW_ID")

def run_flow(flow_input,monitor=True):
    fc = create_flows_client()

    flow = fc.get_flow(flow_id)
    flow_scope = flow['globus_auth_scope']
    
    if monitor:
        flow_action = fc.run_flow(flow_id,flow_scope, flow_input)
        flow_action_id = flow_action['action_id']
        flow_status = flow_action['status']
        print(f'Flow action started with id: {flow_action_id}')

        while flow_status == 'ACTIVE':
            time.sleep(30)
            flow_action = fc.flow_action_status(flow_id, flow_scope, flow_action_id)
            flow_status = flow_action['status']
            print(f'Flow status: {flow_status}')
    return

if __name__ == '__main__':
    flow_input = json.load("./input.json")
    run_flow(flow_input)