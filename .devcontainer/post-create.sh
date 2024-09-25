#!/bin/bash

# install pip packages
pip install --break-system-packages -r requirements.txt

# Install cluster
kind create cluster --config .devcontainer/kind-cluster.yml --wait 300s

# Add Helm chart(s)
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# Create DT API secret for collector
kubectl create secret generic dynatrace-otelcol-dt-api-credentials \
  --from-literal=DT_ENDPOINT=$DT_URL_OBSLAB_LOG_PROBLEM_DETECTION/api/v2/otlp \
  --from-literal=DT_API_TOKEN=$DT_API_TOKEN_OBSLAB_LOG_PROBLEM_DETECTION

# Install RBAC items so collector can talk to k8s API
# to retrieve topology info / pod metadata
kubectl apply -f collector-rbac.yaml

# Install collector
helm upgrade -i dynatrace-collector open-telemetry/opentelemetry-collector -f collector-values.yaml

# Install OpenTelemetry demo app
helm upgrade -i my-otel-demo open-telemetry/opentelemetry-demo -f otel-demo-values.yaml

# Creation Ping
# curl -X POST https://grzxx1q7wd.execute-api.us-east-1.amazonaws.com/default/codespace-tracker \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"repo\": \"$GITHUB_REPOSITORY\",
#     \"demo\": \"obslab-log-problem-detection\",
#     \"codespace.name\": \"$CODESPACE_NAME\"
#   }"
