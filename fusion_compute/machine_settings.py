from dotenv import load_dotenv
from fusion_compute import ENV_PATH
import os

load_dotenv(dotenv_path=ENV_PATH)

def machine_settings():
    machine_settings = {"polaris":{"transfer_endpoint": os.getenv("GLOBUS_ALCF_EAGLE"),
                                    "compute_endpoint": os.getenv("GLOBUS_COMPUTE_POLARIS_ENDPOINT"),
                                    "bin_path": "/eagle/IRIBeta/fusion/bin",
                                    "scratch_path": "/IRIBeta/fusion/",
                                    "facility": "alcf"},
                        "perlmutter":{"transfer_endpoint": os.getenv("GLOBUS_NERSC_PERLMUTTER"),
                                        "compute_endpoint": os.getenv("GLOBUS_COMPUTE_PERLMUTTER_ENDPOINT"),
                                        "bin_path": "/global/common/software/m3739/perlmutter/ionorb/bin/",
                                        "scratch_path": "/pscratch/sd/c/csimpson", ### User needs to change this!
                                        "facility": "nersc"},
                        "summit":{"transfer_endpoint": os.getenv("GLOBUS_OLCF"),
                                "compute_endpoint": os.getenv("GLOBUS_COMPUTE_SUMMIT_ENDPOINT"),
                                "bin_path": "/ccs/home/simpson/bin/",
                                "scratch_path": "/gpfs/alpine2/gen008/scratch/simpson/", ### User needs to change this!
                                "facility": "olcf"},
                        "omega":{"transfer_endpoint": os.getenv("GLOBUS_D3D"),
                                "compute_endpoint": os.getenv("GLOBUS_COMPUTE_OMEGA_SHORT_ENDPOINT"),
                                "bin_path": "/fusion/projects/codes/ionorb/bin",
                                "scratch_path": "/home/simpsonc", ### User needs to change this!
                                "facility": "d3d"}}
    return machine_settings
