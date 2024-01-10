import os
import globus_sdk
from globus_sdk.tokenstorage import SimpleJSONFileAdapter

MY_FILE_ADAPTER = SimpleJSONFileAdapter(os.path.expanduser("~/.sdk-manage-flow.json"))

#SCOPES = [globus_sdk.FlowsClient.scopes.manage_flows]
RESOURCE_SERVER = globus_sdk.FlowsClient.resource_server

# tutorial client ID
# we recommend replacing this with your own client for any production use-cases
# CLIENT_ID = "48f99c28-1a76-4c48-8021-bde33aa6fac7"

#New client id generated for ionorb_demo
CLIENT_ID = "98df61f4-264f-491e-bb7a-6b930bf050c0"


NATIVE_CLIENT = globus_sdk.NativeAppAuthClient(CLIENT_ID)


def do_login_flow(scope):
    NATIVE_CLIENT.oauth2_start_flow(requested_scopes=scope, refresh_tokens=True)
    authorize_url = NATIVE_CLIENT.oauth2_get_authorize_url()
    print(f"Please go to this URL and login:\n\n{authorize_url}\n")
    auth_code = input("Please enter the code here: ").strip()
    tokens = NATIVE_CLIENT.oauth2_exchange_code_for_tokens(auth_code)
    return tokens


def get_authorizer(flow_id=None):
    if flow_id is None:
        scopes = [globus_sdk.FlowsClient.scopes.manage_flows]
    else:
        scopes = globus_sdk.SpecificFlowClient(flow_id).scopes
        scopes = scopes.user

    # try to load the tokens from the file, possibly returning None
    if MY_FILE_ADAPTER.file_exists():
        if flow_id is None:
            tokens = MY_FILE_ADAPTER.get_token_data(RESOURCE_SERVER)
        else:
            tokens = MY_FILE_ADAPTER.get_token_data(flow_id)
    else:
        tokens = None

    if tokens is None:
        # do a login flow, getting back initial tokens
        response = do_login_flow(scopes)
        # now store the tokens and pull out the correct token
        MY_FILE_ADAPTER.store(response)
        if flow_id is None:
            tokens = response.by_resource_server[RESOURCE_SERVER]
        else:
            tokens = response.by_resource_server[flow_id]

    return globus_sdk.RefreshTokenAuthorizer(
        tokens["refresh_token"],
        NATIVE_CLIENT,
        access_token=tokens["access_token"],
        expires_at=tokens["expires_at_seconds"],
        on_refresh=MY_FILE_ADAPTER.on_refresh,
    )


def get_flows_client(flow_id=None):
    if flow_id is None:
        return globus_sdk.FlowsClient(authorizer=get_authorizer())
    else:
        authorizer = get_authorizer(flow_id=flow_id)
        return globus_sdk.SpecificFlowClient(flow_id, authorizer=authorizer)
    
