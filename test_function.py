import globus_compute_sdk
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="./fusion.env")

polaris_ep = os.getenv("GLOBUS_COMPUTE_ENDPOINT")
func = os.getenv("GLOBUS_FUNCTION_ID")

gce = globus_compute_sdk.Executor(endpoint_id=polaris_ep)
future = gce.submit_to_registered_function(args=[], function_id=func)
print(future.result())