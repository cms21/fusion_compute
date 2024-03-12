import os

__version__ = "0.0.1"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(ROOT_DIR,"../fusion.env")

from fusion_compute.start_fusion_flow import run_flow
from fusion_compute.utils import get_flows_client
from fusion_compute.utils import get_specific_flow_client
from fusion_compute.machine_settings import machine_settings
from fusion_compute.functions import register_function
from fusion_compute.flows import *

__all__ = [
    "run_flow",
    "get_flows_client",
    "get_specific_flow_client",
    "machine_settings",
    "register_function"
]