#!/bin/bash

# Install
kind create cluster --config .devcontainer/kind-cluster.yml --wait 300s

# Creation Ping
# TODO: Enable
# curl -X POST https://grzxx1q7wd.execute-api.us-east-1.amazonaws.com/default/codespace-tracker \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"repo\": \"$GITHUB_REPOSITORY\",
#     \"demo\": \"obslab-log-problem-detection\",
#     \"codespace.name\": \"$CODESPACE_NAME\"
#   }"
