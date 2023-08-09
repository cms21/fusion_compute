import globus_compute_sdk
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../fusion.env")

gce = globus_compute_sdk.Executor(endpoint_id=os.getenv("GLOBUS_COMPUTE_ENDPOINT"))
future = gce.submit_to_registered_function(args=[], function_id=os.getenv("GLOBUS_FUNCTION_ID"))
print(future.result())