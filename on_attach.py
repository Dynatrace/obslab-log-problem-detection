from utils import *

# This runs every time a user attaches or re-attaches to the environment.
# It is required due to the way docker networking and IPs work.
# Without this, `kubectl get nodes` can fail.
# This is triggered automatically via the on_attach hook in devcontainer.json.

configureClusterConnection()
