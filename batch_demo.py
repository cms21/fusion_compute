from globus_automate_client import create_flows_client
from start_fusion_flow import run_flow, endpoint_active
import json, time, uuid, os

if __name__ == '__main__':

    nruns = 16
    injection_wait_time = 1
    tags = []
    json_input_path = "./input.json"
    flow_input = json.load(open(json_input_path))
    label_base = f"fusion-batch-test"

    test_tag = uuid.uuid4()
    tags.append(str(test_tag))

    print(f"nruns: {nruns}")
    print(f"injection_time: {injection_wait_time} s")
    print(f"label: {label_base}")
    print(f"test_series_tag_id: {test_tag}")

    if endpoint_active(flow_input["input"]["compute_endpoint_id"]):
        fc = create_flows_client()
        flow_actions = []
        for i in range(nruns):
            label = label_base+f"-{i+1}/{nruns}"
            source_path = "/csimpson/polaris/fusion"
            destination_path = f"/IRIBeta/test_runs/batch_test/{test_tag}/{i}"
            return_path = f"/csimpson/polaris/fusion_return/{test_tag}/{i}"
            run_flow(json_input_path, source_path, destination_path, return_path, label=label, tags=tags, flow_client=fc)
            print(f"Running {label}")
            time.sleep(injection_wait_time)
