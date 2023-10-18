from dotenv import load_dotenv
import os
from start_fusion_flow import machine_settings

load_dotenv(dotenv_path="./fusion.env")

def grant_consents(machines=machine_settings.keys(),print_url=True, grant_consents=False):

    FLOW_ID = os.getenv("GLOBUS_FLOW_ID")
    UNDERSCORE_FLOW_ID = "_".join(FLOW_ID.split("-"))
    
    collections = [os.getenv("GLOBUS_TRANSFER_ENDPOINT_SRC")]
    for machine in machines:
        collections.append(machine_settings[machine]["transfer_endpoint"])
    
    for COLLECTION_ID in collections:
        auth_url = f"https://auth.globus.org/scopes/{FLOW_ID}/flow_{UNDERSCORE_FLOW_ID}_user[https://auth.globus.org/scopes/actions.globus.org/transfer/transfer[urn:globus:auth:scope:transfer.api.globus.org:all[*https://auth.globus.org/scopes/{COLLECTION_ID}/data_access]]]"
        auth_command = f"globus session consent --no-local-server {auth_url}"
        if print_url:
            print(auth_command+"\n")
        if grant_consents:
            os.system(auth_command)

grant_consents(grant_consents=True)