import requests
import datetime
import subprocess
import glob
import time
import os
import json
import yaml
import hashlib
from loguru import logger
import subprocess
import sys
from dotenv import load_dotenv, set_key
import os, re, subprocess, getpass

try:
    from playwright.sync_api import Page, expect, FrameLocator
except ImportError:
    # Keep normal setup working when testing dependencies are not installed.
    class Page:
        pass

    class FrameLocator:
        pass

    def expect(*args, **kwargs):
        raise ImportError(
            "Playwright testing dependencies are not installed. "
            "Install requirements.testing.txt to use testing utility functions."
        )

from loguru import logger

try:
    import pytest
except ImportError:
    pytest = None

import requests
import datetime


def _testing_fail(message: str):
    if pytest is not None:
        pytest.fail(message)
    raise RuntimeError(
        f"{message} Install requirements.testing.txt to run testing utility functions."
    )

loaded = load_dotenv()

RUNME_CLI_VERSION = "3.16.10"
REPOSITORY_NAME = os.environ.get("RepositoryName", "obslab-log-problem-detection")
BASE_DIR = os.environ.get("BASE_DIR", f"/workspaces/{REPOSITORY_NAME}")
DEV_MODE = os.environ.get("DEV_MODE", "FALSE").upper() # This is a string. NOT a bool.
TESTING_DYNATRACE_USER_EMAIL = os.environ.get("TESTING_DYNATRACE_USER_EMAIL", "")
TESTING_DYNATRACE_USER_PASSWORD = os.environ.get("TESTING_DYNATRACE_USER_PASSWORD", "")
WAIT_TIMEOUT = 30000
SECTION_TYPE_METRICS = "Metrics"
SECTION_TYPE_DQL = "DQL"
SECTION_TYPE_CODE = "Code"
SECTION_TYPE_MARKDOWN = "Markdown"

# If GITHUB_USER is unset, codespace is running locally
# In which case, attempt to load the .env file
# Otherwise the details are pulled from the `secrets` block
# in devcontainer.json (provided via the GitHub UI form)
# In that case, loading the .env file is uneccessary
# As the env vars are directly injected / set by Github
GITHUB_USER = os.environ.get("GITHUB_USER", "")
if GITHUB_USER == "":
    # Running codespace locally
    # so load the .env file
    loaded = load_dotenv()
    if not loaded:
        logger.error("Did you create a .env file?")

DT_ENVIRONMENT_ID = os.environ.get("DT_ENVIRONMENT_ID", "")
DT_ENVIRONMENT_TYPE = os.environ.get("DT_ENVIRONMENT_TYPE", "live")
DT_API_TOKEN = os.environ.get("DT_API_TOKEN", "")

# GEOLOCATION_DEV = "GEOLOCATION-0A41430434C388A9"
# GEOLOCATION_SPRINT = "GEOLOCATION-3F7C50D0C9065578"
# GEOLOCATION_LIVE = "GEOLOCATION-45AB48D9D6925ECC"
# Live locations
# GEOLOCATION-E7F41460B2A0E4B3 - Amsterdam (Azure)
# GEOLOCATION-45AB48D9D6925ECC - Frankfurt (AWS)
# GEOLOCATION-2A90D19543B5871E - Groningen (Google)
# GEOLOCATION-871416B95457AB88 - London (Alibaba)
# SSO_TOKEN_URL_DEV = "https://sso-dev.dynatracelabs.com/sso/oauth2/token"
# SSO_TOKEN_URL_SPRINT = "https://sso-sprint.dynatracelabs.com/sso/oauth2/token"
# SSO_TOKEN_URL_LIVE = "https://sso.dynatrace.com/sso/oauth2/token"

# If any of these words are found in command execution output
# The printing of the output to console will be suppressed
# Add words here to block more things
SENSITIVE_WORDS = ["secret", "secrets", "token", "tokens", "generate-token"]

# BACKSTAGE_PORT_NUMBER = 30105
# ARGOCD_PORT_NUMBER = 30100
# DEMO_APP_PORT_NUMBER = 80

# STANDARD_TIMEOUT="300s"
# WAIT_FOR_ARTIFACT_TIMEOUT = 60
# WAIT_FOR_ACCOUNTS_TIMEOUT = 60

# COLLECTOR_WAIT_TIMEOUT_SECONDS = 30
# OPENTELEMETRY_COLLECTOR_ENDPOINT = "http://localhost:4318"
CODESPACE_NAME = os.environ.get("CODESPACE_NAME")

GITHUB_REPO_NAME = os.environ.get("RepositoryName", "") # eg. mclass
GITHUB_ORG_SLASH_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", GITHUB_REPO_NAME) # eg. yourOrg/yourRepo
GITHUB_DOT_COM_REPO = f"https://github.com/{GITHUB_ORG_SLASH_REPOSITORY}.git"
GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
# DT_OAUTH_CLIENT_ID = os.environ.get("DT_OAUTH_CLIENT_ID")
# DT_OAUTH_CLIENT_SECRET = os.environ.get("DT_OAUTH_CLIENT_SECRET")
# DT_OAUTH_ACCOUNT_URN = os.environ.get("DT_OAUTH_ACCOUNT_URN")

def run_command(args, ignore_errors=False):
    output = subprocess.run(args, capture_output=True, text=True, encoding="UTF8")

    # Secure coding. Don't print sensitive info to console.
    # Find common elements between blocked words and args.
    # Only print output if not found.
    # If found, it means the output of this command (as given in args) is expected to be sensitive
    # So do not print.
    set1 = set(args)
    set2 = set(SENSITIVE_WORDS)
    common_elems = (set1 & set2)
    if not common_elems:
        logger.info(output.stdout)

    # Annoyingly, if git has nothing to commit
    # it exits with a returncode == 1
    # So ignore any git errors but exit for all others
    if not ignore_errors and output.returncode > 0:
        exit(f"Got an error! Return Code: {output.returncode}. Error: {output.stderr}. Stdout: {output.stdout}. Exiting.")
    return output

def do_file_replace(pattern="", find_string="", replace_string="", recursive=False):
    for filepath in glob.iglob(pattern, recursive=recursive):
        TARGET_FILE = False
        with open(filepath, "r") as file: # open file in read mode only first
            file_content = file.read()
            if find_string in file_content:
                TARGET_FILE = True
        # Replace the text
        file_content = file_content.replace(find_string, replace_string)

        if TARGET_FILE:
            with open(filepath, "w") as file: # now open in write mode and write
                file.write(file_content)

def git_commit(target_file="", commit_msg="", push=False):
    output = run_command(["git", "add", target_file], ignore_errors=True)
    output = run_command(["git", "commit", "-m", commit_msg], ignore_errors=True)
    if push:
        output = run_command(["git", "push"], ignore_errors=True)

# Whereas the kubectl wait command can be used to wait for EXISTING artifacts (eg. deployments) to be READY.
# kubectl wait will error if the artifact DOES NOT EXIST YET.
# This function first waits for it to even exist
# eg. wait_for_artifact_to_exist(namespace="default", artifact_type="deployment", artifact_name="backstage")
# def wait_for_artifact_to_exist(namespace="default", artifact_type="", artifact_name=""):
#     count = 1
#     get_output = run_command(["kubectl", "-n", namespace, "get", f"{artifact_type}/{artifact_name}"], ignore_errors=True)

#     # if artifact does not exist, important output will be in stderr
#     # if artifact DOES exist, use stdout
#     if get_output.stderr != "":
#         get_output = get_output.stderr
#     else:
#         get_output = get_output.stdout

#     print(get_output)

#     while count < WAIT_FOR_ARTIFACT_TIMEOUT and "not found" in get_output:
#         print(f"Waiting for {artifact_type}/{artifact_name} in {namespace} to exist. Wait count: {count}")
#         count += 1
#         get_output = run_command(["kubectl", "-n", namespace, "get", f"{artifact_type}/{artifact_name}"], ignore_errors=True)
#         # if artifact does not exist, important output will be in stderr
#         # if artifact DOES exist, use stdout
#         if get_output.stderr != "":
#             get_output = get_output.stderr
#         else:
#             get_output = get_output.stdout
#         print(get_output)
#         time.sleep(1)

# def get_otel_collector_endpoint():
#     return OPENTELEMETRY_COLLECTOR_ENDPOINT

def get_github_org(github_repo):
    return github_repo[:github_repo.index("/")]

def hash_string(input_str, charset="UTF-8", algorithm="SHA256"):
    hash_factory = hashlib.new(algorithm)
    hash_factory.update(input_str.encode(charset))
    return hash_factory.hexdigest()

##############################
# DT FUNCTIONS

# def send_log_to_dt_or_otel_collector(success, msg_string="", dt_api_token="", endpoint=get_otel_collector_endpoint(), destroy_codespace=False, dt_tenant_live=""):

#     attributes_list = [{"key": "success", "value": { "boolean": success }}]

#     timestamp = str(time.time_ns())

#     if "dynatrace" in endpoint:
#         # Local collector not available
#         # Send directly to cluster
#         payload = {
#             "content": msg_string,
#             "log.source": "testharness.py",
#             "severity": "error"
#         }

#         headers = {
#             "accept": "application/json; charset=utf-8",
#             "Authorization": f"Api-Token {dt_api_token}",
#             "Content-Type": "application/json"
#         }

#         requests.post(f"{dt_tenant_live}/api/v2/logs/ingest", 
#           headers = headers,
#           json=payload,
#           timeout=5
#         )
#     else: # Send via local OTEL collector
#         payload = {
#             "resourceLogs": [{
#                 "resource": {
#                     "attributes": []
#                 },
#                 "scopeLogs": [{
#                     "scope": {},
#                     "logRecords": [{
#                         "timeUnixNano": timestamp,
#                         "body": {
#                             "stringValue": msg_string
#                         },
#                         "attributes": attributes_list,
#                         "droppedAttributesCount": 0
#                     }]
#                 }]
#             }]
#         }

#         requests.post(f"{endpoint}/v1/logs", headers={ "Content-Type": "application/json" }, json=payload, timeout=5)

#     # If user wishes to immediately
#     # destroy the codespace, do it now
#     # Note: Log lines inside here must have destroy_codespace=False to avoid circular calls
#     destroy_codespace = False # DEBUG: TODO remove. Temporarily override while developing
#     if destroy_codespace:
#         send_log_to_dt_or_otel_collector(success=True, msg_string=f"Destroying codespace: {CODESPACE_NAME}", destroy_codespace=False, dt_tenant_live=dt_tenant_live)

#         destroy_codespace_output = subprocess.run(["gh", "codespace", "delete", "--codespace", CODESPACE_NAME], capture_output=True, text=True)

#         if destroy_codespace_output.returncode == 0:
#             send_log_to_dt_or_otel_collector(success=True, msg_string=f"codespace {CODESPACE_NAME} deleted successfully", destroy_codespace=False, dt_tenant_live=dt_tenant_live)
#         else:
#             send_log_to_dt_or_otel_collector(success=False, msg_string=f"failed to delete codespace {CODESPACE_NAME}. {destroy_codespace_output.stderr}", destroy_codespace=False, dt_tenant_live=dt_tenant_live)

# def get_geolocation(dt_env_type="live"):
#     if dt_env_type.lower() == "dev":
#         return GEOLOCATION_DEV
#     elif dt_env_type.lower() == "sprint":
#         return GEOLOCATION_SPRINT
#     elif dt_env_type.lower() == "live":
#         return GEOLOCATION_LIVE
#     else:
#         return None

# def get_sso_token_url(dt_env_type="live"):
#     if dt_env_type.lower() == "dev":
#         return SSO_TOKEN_URL_DEV
#     elif dt_env_type.lower() == "sprint":
#         return SSO_TOKEN_URL_SPRINT
#     elif dt_env_type.lower() == "live":
#         return SSO_TOKEN_URL_LIVE
#     else:
#         return None
    
def create_dt_api_token(token_name, scopes, dt_api_token, dt_tenant_live):

    # Automatically expire tokens 1 day in future.
    time_future = datetime.datetime.now() + datetime.timedelta(days=1)
    expiry_date = time_future.strftime("%Y-%m-%dT%H:%M:%S.999Z")

    headers = {
        "accept": "application/json; charset=utf-8",
        "content-type": "application/json; charset=utf-8",
        "authorization": f"api-token {dt_api_token}"
    }

    payload = {
        "name": token_name,
        "scopes": scopes,
        "expirationDate": expiry_date
    }

    resp = requests.post(
        url=f"{dt_tenant_live}/api/v2/apiTokens",
        headers=headers,
        json=payload
    )

    if resp.status_code != 201:
        exit(f"Cannot create DT API token: {token_name}. Response was: {resp.status_code}. {resp.text}. Exiting.")

    return resp.json()['token']

def build_dt_urls(dt_env_id, dt_env_type="live"):
    if dt_env_type.lower() == "live":
        dt_tenant_apps = f"https://{dt_env_id}.apps.dynatrace.com"
        dt_tenant_live = f"https://{dt_env_id}.live.dynatrace.com"
    else:
      dt_tenant_apps = f"https://{dt_env_id}.{dt_env_type}.apps.dynatrace.com"
      dt_tenant_live = f"https://{dt_env_id}.{dt_env_type}.dynatrace.com"

    # if ENVIRONMENT is "dev" or "sprint"
    # ".dynatracelabs.com" not ".dynatrace.com"
    if dt_env_type.lower() == "dev" or dt_env_type.lower() == "sprint":
        dt_tenant_apps = dt_tenant_apps.replace(".dynatrace.com", ".dynatracelabs.com")
        dt_tenant_live = dt_tenant_live.replace(".dynatrace.com", ".dynatracelabs.com")
    
    return dt_tenant_apps, dt_tenant_live

def _buildDTURLsAndPersistToDisk():
    dt_tenant_apps, dt_tenant_live = build_dt_urls(DT_ENVIRONMENT_ID, DT_ENVIRONMENT_TYPE)
    set_key(dotenv_path=f"{BASE_DIR}/.env", key_to_set="DT_URL", value_to_set=dt_tenant_live, export=True)

# Run the above function
_buildDTURLsAndPersistToDisk()

# def get_sso_auth_token(sso_token_url, oauth_client_id, oauth_client_secret, oauth_urn, permissions):
    
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded"
#     }
#     oauth_body = {
#         "grant_type": "client_credentials",
#         "client_id": oauth_client_id,
#         "client_secret": oauth_client_secret,
#         "resource": oauth_urn,
#         "scope": permissions
#     }

#     ##############################
#     # Step 1: Get Access Token
#     ##############################
#     access_token_resp = requests.post(
#         url=sso_token_url,
#         data=oauth_body
#     )

#     if access_token_resp.status_code != 200:
#         print(f"{access_token_resp.json()}")
#         return "OAuth error occurred. Data NOT sent. Please investigate."

#     access_token_json = access_token_resp.json()
#     access_token_value = access_token_json['access_token']

#     return access_token_value

# TODO: This is naieve. Multiple POSTs for the same content creates duplicated. Improve.
# def upload_dt_document_asset(sso_token_url, path, name, type, dt_tenant_apps, upload_content_type="application/json"):

#     if type != "notebook" and type != "dashboard":
#         exit("type must be one of these values: [notebook, dashboard]")

#     endpoint = f"{dt_tenant_apps}/platform/document/v1/documents"
#     permissions = "document:documents:write"

#     oauth_access_token = get_sso_auth_token(sso_token_url=sso_token_url, oauth_client_id=DT_OAUTH_CLIENT_ID, oauth_client_secret=DT_OAUTH_CLIENT_SECRET, oauth_urn=DT_OAUTH_ACCOUNT_URN, permissions=permissions)

#     headers = {
#         "accept": "application/json",
#         "Authorization": f"Bearer {oauth_access_token}"
#     }

#     with open(path, mode="r", encoding="UTF-8") as f:

#         file_content = f.read()

#         parameters = {
#             "name": name,
#             "type": type
#         }

#         upload_resp = requests.post(
#             url=endpoint,
#             params=parameters,
#             files={"content": (path, f"{file_content}", upload_content_type)},
#             headers=headers
#         )

#     return upload_resp

# def upload_dt_workflow_asset(sso_token_url, path, name, dt_tenant_apps, upload_content_type="application/json"):

#     endpoint = f"{dt_tenant_apps}/platform/automation/v1/workflows"
#     permissions = "automation:workflows:write"

#     oauth_access_token = get_sso_auth_token(sso_token_url=sso_token_url, oauth_client_id=DT_OAUTH_CLIENT_ID, oauth_client_secret=DT_OAUTH_CLIENT_SECRET, oauth_urn=DT_OAUTH_ACCOUNT_URN, permissions=permissions)

#     headers = {
#         "accept": "application/json",
#         "Authorization": f"Bearer {oauth_access_token}"
#     }

#     with open(path, mode="r", encoding="UTF-8") as f:

#         file_content = f.read()
#         file_json = json.loads(file_content)

#         upload_resp = requests.post(
#             url=endpoint,
#             json=file_json,
#             headers=headers
#         )

#     return upload_resp

def send_startup_ping(demo_name=""):
    ## 1. Take lowercase GITHUB_ORG_SLASH_REPO and lowercase it.
    ## 2. For user privacy, calculate an irreversible one-way hash of this string
    hashed_org_slash_repo = hash_string(input_str=GITHUB_ORG_SLASH_REPOSITORY.lower(), charset="UTF-8", algorithm="SHA256")

    # Build content and send request
    url = "https://grzxx1q7wd.execute-api.us-east-1.amazonaws.com/default/codespace-tracker"

    headers = {
        "User-Agent": "GitHub",
        "Content-Type": "application/json"
    }

    body = {
        "repo": hashed_org_slash_repo,
        "testing": False,
        "tenant": DT_ENVIRONMENT_ID,
        "demo": demo_name,
        "codespace.name": CODESPACE_NAME
    }

    resp = requests.post(
        url=url,
        headers=headers,
        json=body
    )

# Cluster is created
# But due to running locally in docker
# the IPs aren't correct so kubectl get nodes won't work
# This function fixes this
def configureClusterConnection():
    with open(f"{BASE_DIR}/.devcontainer/kind-cluster.yml", 'r') as file:
        data = yaml.safe_load(file)

    # Access specific values like a dictionary
    cluster_name = data['name']

    # 3) Determine current container ID (hostname)
    try:
        container_id = subprocess.run(["hostname"], capture_output=True).stdout.strip()
        if not container_id:
            raise RuntimeError("Empty hostname")
        logger.info(f"Container ID (hostname): {container_id}")
    except Exception as e:
        logger.error("Failed to obtain hostname/container id:", e, file=sys.stderr)
        sys.exit(1)
    
    # Start container if it isn't already
    logger.info(f"Starting {cluster_name}-control-plane in case it is stopped...")
    try:
        subprocess.run(["docker", "start", f"{cluster_name}-control-plane"])
    except Exception as e:
        logger.info(f"Caught exception trying to start {cluster_name}-control-plane. Perhaps it is already running?")
        logger.error(e)

    # 3) Connect this devcontainer to the kind network (ignore error if already connected)
    logger.info(f"Connecting container {container_id} to Docker network {cluster_name} (if not already connected)...")
    proc = subprocess.run(["docker", "network", "connect", "kind", container_id], check=False, capture_output=True)
    if proc.returncode == 0:
        logger.info(f"Connected to '{cluster_name}' network.")
    else:
        # Docker returns non-zero if already connected or other issues
        # We mimic the bash behaviour: ignore the error
        stderr = proc.stderr.strip() if proc.stderr else ""
        print(f"Ignored error while connecting to network (return code {proc.returncode}): {stderr}")

    # 4) Get the kind-control-plane internal IP on the `cluster_name` network
    try:
        logger.info(f"Inspecting '{cluster_name}-control-plane' container to find IP on '{cluster_name}' network...")
        inspect_out = subprocess.run(["docker", "inspect", f"{cluster_name}-control-plane"], capture_output=True).stdout
        info = json.loads(inspect_out)
        # info is a list; take the first element
        net_info = info[0]["NetworkSettings"]["Networks"]
        logger.info(net_info)
        # This SHOULD really be 'kind'
        # and not the cluster name because kind calls its network `kind`
        if 'kind' not in net_info:
            raise KeyError("Network 'kind' not present in kind-control-plane networks")
        kind_ip = net_info["kind"]["IPAddress"]
        if not kind_ip:
            raise RuntimeError(f"Empty IP address for {cluster_name}-control-plane on 'kind' network")
        logger.info(f"Found {cluster_name}-control-plane IP on 'kind' network: {kind_ip}")
    except (subprocess.CalledProcessError, KeyError, IndexError, ValueError, RuntimeError) as e:
        logger.error(f"Failed to get {cluster_name}-control-plane IP:", e, file=sys.stderr)
        sys.exit(1)

    # 5) Update kubeconfig to use the internal IP instead of 127.0.0.1
    server_url = f"https://{kind_ip}:6443"
    try:
        logger.info(f"Updating kubeconfig cluster 'kind-{cluster_name}' to use API server {server_url} ...")
        subprocess.run(["kubectl", "config", "set-cluster", f"kind-{cluster_name}", f"--server={server_url}"], check=True)
        logger.info("kubeconfig updated.")
    except subprocess.CalledProcessError as e:
        logger.error("Failed to update kubeconfig:", e, file=sys.stderr)
        sys.exit(1)

def createKubernetesCluster():

    # For safety, delete any existing clusters
    # Note, as standard (written by the template) this function is only triggered in the ENVIRONMENT_installer.py
    # Which in turn only fires on creation
    # So this logic does NOT fire when a user reconnects to an existing container
    try:
        run_command(["kind", "delete", "clusters", "-A"], ignore_errors=True)
    except:
        pass
    
    try:
        # 1) Create kind cluster
        logger.info("Creating kind cluster...")
        
        subprocess.run([
            "kind", "create", "cluster",
            "--config", f"{BASE_DIR}/.devcontainer/kind-cluster.yml",
            "--wait", "30s"
        ], check=True)

    except subprocess.CalledProcessError as e:
        logger.error("Error creating kind cluster:", e, file=sys.stderr)
        # Decide whether to continue or exit; we exit here because subsequent steps depend on the cluster
        sys.exit(1)

    logger.info("Kind cluster creation completed.")

def get_steps(filename):
    with open(filename, mode="r") as steps_file:
        steps = steps_file.readlines()
        steps_clean = []

        for step in steps:
            step = step.strip()
            steps_clean.append(step)
    
    return steps_clean

############################
# Testing related functions below

def get_app_frame_and_locator(page: Page):
    frame_locator = page.frame_locator('[data-testid="app-iframe"]')
    frame = frame_locator.owner
    return frame_locator, frame

def wait_for_app_to_load(page: Page):
    page.wait_for_load_state('networkidle')
    frame_locator = page.frame_locator('[data-testid="app-iframe"]')
    frame = frame_locator.locator('body')
    expect(frame).to_be_visible()

    frame_locator, frame = get_app_frame_and_locator(page)
    expect(frame).to_have_attribute(name="data-isloaded", value="true")
    frame.locator("#content_root").is_visible()

    return frame_locator, frame

def login(page: Page):
    page.goto("https://sso.dynatrace.com")
    page.get_by_test_id("text-input").fill(TESTING_DYNATRACE_USER_EMAIL)
    page.wait_for_selector('[data-id="email_submit"]').click()
    page.locator('[data-id="password_login"]').fill(TESTING_DYNATRACE_USER_PASSWORD)
    page.locator('[data-id="sign_in"]').click(timeout=WAIT_TIMEOUT)
    page.wait_for_url("**/ui/**")
    expect(page.locator("title", has_text=DT_ENVIRONMENT_ID).first)

    # Wait for app to load
    wait_for_app_to_load(page)

def open_search_menu(page: Page):
    page.get_by_test_id("dock-search").click()
    #expect(page.locator("h1")).to_have_text("Quickly find your apps, documents, entities, and more", timeout=WAIT_TIMEOUT)
    expect(page.get_by_placeholder("Search and navigate your ENVIRONMENT")).to_be_attached(timeout=WAIT_TIMEOUT)

def search_for(page: Page, search_term: str):
    page.get_by_label("Search query").fill(search_term)
    expect(page.get_by_label("Result details")).to_be_visible(timeout=WAIT_TIMEOUT)
    # Expect the search result to appear in the menu bar
    # Create case-insensitive regex pattern
    span = page.locator(f'span:has-text("{search_term.capitalize()}")').first
    expect(span).to_be_visible(timeout=WAIT_TIMEOUT)

def open_app_from_search_modal(page: Page, app_name: str):
    page.locator(f"[id='apps:dynatrace.{app_name}']").click()
    page.wait_for_url(f"**/dynatrace.{app_name}/**")
    expect(page).to_have_title(re.compile(app_name, re.IGNORECASE))
    wait_for_app_to_load(page)

def get_app_frame_and_locator(page: Page):
    frame_locator = page.frame_locator('[data-testid="app-iframe"]')
    frame = frame_locator.owner
    return frame_locator, frame

def create_new_document(page: Page, close_microguide: bool = False):

    wait_for_app_to_load(page)

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    app_frame_locator.get_by_test_id("new-document-button").first.click()
    expect(app_frame).to_have_attribute(name="data-isloaded", value="true")

    if close_microguide:
        try:
            logger.info("Trying to close the microguide...")
            app_frame.get_by_label("Close microguide").click(timeout=1000)
        except:
            logger.info("Microguide didn't show. That's OK. Proceeding.")

def add_document_section(page, section_type_text):

    wait_for_app_to_load(page)

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    if section_type_text == SECTION_TYPE_DQL:
        logger.info("Using key combination Shift+D for DQL tile")
        page.keyboard.press("Shift+D")
    elif section_type_text == SECTION_TYPE_CODE:
        logger.info("Using key combination Shift+C for Code tile")
        page.keyboard.press("Shift+C")
    elif section_type_text == SECTION_TYPE_MARKDOWN:
        logger.info("Using key combination Shift+M for Markdown tile")
        page.keyboard.press("Shift+M")
    else:
        page.keyboard.press("ControlOrMeta+Shift+Enter")
        expect(app_frame_locator.get_by_text("Create new section")).to_be_visible(timeout=WAIT_TIMEOUT)
        logger.info(f"Clicking {section_type_text}")
        app_frame_locator.get_by_text(section_type_text, exact=False).first.click(timeout=WAIT_TIMEOUT)

def enter_dql_query(page, dql_query, section_index, validate):

    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    section = app_frame_locator.locator(f"[data-testid-section-index=\"{section_index}\"]")
    
    #section.get_by_label("Enter a DQL query").type(dql_query)
    section.get_by_role("textbox").fill(dql_query)

    if validate:
        validate_document_section_has_data(page, section_index)

def validate_document_section_has_data(page: Page, section_index):

    wait_for_app_to_load(page)
    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    logger.info(f"Validating that section_index {section_index} has data")

    section = app_frame_locator.locator(f"[data-testid-section-index=\"{section_index}\"]")

    # Click the Run button
    section.get_by_test_id("run-query-button").click(timeout=WAIT_TIMEOUT)

    # wait for DQL to finish
    # if this times out, either query took too long
    # of the query was invalid
    try:
        section.get_by_test_id("result-container").wait_for(timeout=WAIT_TIMEOUT)
    except:
        _testing_fail("Either query timed out or an invalid query was provided.")


    # If we get here
    # query executed
    # see if there valid data returned

    # Try to find the "no data" <h6>
    # Remember, NOT finding this is actually a good thing
    # Because then you DO have data
    no_data_heading = section.locator("h6")
    # If the chart graphic does not appear
    # Then the data is not available in Dynatrace
    # and we should error and exit.
    if no_data_heading.is_visible():
        _testing_fail(f"No data found in section_index={section_index}")
    else:
        logger.debug(f"[DEBUG] 1 Data found in section_index={section_index}")

# Specific function to add a metric to a metric type chart
# Note: This does NOT click the "Run query" button
# For data validation, use the valudate_document_section_has_data function
def add_metric(page, search_term, metric_text, section_index, validate):
    
    wait_for_app_to_load(page)
    app_frame_locator, app_frame = get_app_frame_and_locator(page)

    app_frame_locator.get_by_label("Metric key").first.click()

    logger.info(f"Typing `{search_term}` into the box")
    app_frame_locator.get_by_test_id("text-input").fill(search_term)

    app_frame_locator.get_by_label(metric_text).last.click()
    logger.info(f"Selecting {metric_text} from list")    

    # If user has chosen to validate
    # That this metric has data points
    if validate:
        validate_document_section_has_data(page, section_index)


def delete_document(page):
    app_frame_locator, app_frame = get_app_frame_and_locator(page)
    app_frame_locator.get_by_label("Document actions").last.click(timeout=WAIT_TIMEOUT)
    app_frame_locator.get_by_text("Move to trash").last.wait_for(timeout=WAIT_TIMEOUT)
    app_frame_locator.get_by_text("Move to trash").last.click(timeout=WAIT_TIMEOUT)

# This function takes a snippet name
# and retrieves the DQL using runme
# eg. { "name": "fetch events dql"}
def retrieve_dql_query(snippet_name):
    output = subprocess.run(["runme", "print", snippet_name], capture_output=True, text=True)
    return output.stdout
# Install the Dynatrace collector using Helm
def installDynatraceCollector():
    DT_URL = os.environ.get("DT_URL","")
    run_command(["kubectl", "create", "secret", "generic", "dynatrace-otelcol-dt-api-credentials",
                 f"--from-literal=DT_ENDPOINT={DT_URL}/api/v2/otlp",
                 f"--from-literal=DT_API_TOKEN={DT_API_TOKEN}"], ignore_errors=True)
    run_command(["helm", "repo","add", "open-telemetry", "https://open-telemetry.github.io/opentelemetry-helm-charts"], ignore_errors=True)
    run_command(["helm", "repo", "update"])
    run_command(["helm", "upgrade", "-i", "dynatrace-collector", "open-telemetry/opentelemetry-collector", "-f", "collector-values.yaml"], ignore_errors=True)
    run_command(["kubectl", "apply", "-f", "collector-rbac.yaml"])

def installOTELDemoApp():
    run_command(["helm", "upgrade", "-i", "my-otel-demo", "open-telemetry/opentelemetry-demo", "-f", "otel-demo-values.yaml"], ignore_errors=True)

def addHelmChart(name, url, update):
    run_command(["helm", "repo", "add", name, url])
    if update:
        run_command(["helm", "repo", "update"])
def helmInstall(name, url, namespace, values_file=None, atomic=False):
    command = ["helm", "upgrade", "-i", name, url, f"--namespace={namespace}", f"--atomic={atomic}"]
    if values_file:
        command.append(f"--values={values_file}")
    run_command(command)


def createNamespace(name):
    run_command(["kubectl", "create", "namespace", name])

# At the end of it all, load in whatever is currently in .env
load_dotenv()

DT_URL = os.environ.get("DT_URL")