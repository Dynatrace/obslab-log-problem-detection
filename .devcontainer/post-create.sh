#!/bin/bash

#############################################################################
# install pip packages
pip install --break-system-packages -r requirements.txt

#############################################################################
# Install cluster
kind create cluster --config .devcontainer/kind-cluster.yml --wait 300s

#############################################################################
# Add Helm chart(s)
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

#############################################################################
# Build URL from parts
full_apps_url="https://${DT_ENV_ID_OBSLAB_LOG_PROBLEM_DETECTION}"
full_gen2_url=""

if [ "${DT_ENV_OBSLAB_LOG_PROBLEM_DETECTION}" = "dev" ]; then
  echo "environment is dev"
  full_apps_url+=".dev.apps.dynatracelabs.com"
  # Remove apps.
  full_gen2_url=${full_apps_url/apps.}
elif [ "${DT_ENV_OBSLAB_LOG_PROBLEM_DETECTION}" = "sprint" ]; then
  echo "environment is sprint"
  full_apps_url+=".sprint.apps.dynatracelabs.com"
  # Remove apps.
  full_gen2_url=${full_apps_url/apps.}
else
  echo "DT_ENV_OBSLAB_LOG_PROBLEM_DETECTION is either 'live' or some other value. Defaulting to live"
  full_apps_url+=".apps.dynatrace.com"
  full_gen2_url=${full_apps_url/.apps./.live.}
fi

#############################################################################
# Replace placeholders for notebook
sed -i "s@FULL_APPS_URL_PLACEHOLDER@$full_apps_url@g" otel-demo-values.yaml
sed -i "s@DOCUMENT_ID_PLACEHOLDER@$DT_NOTEBOOK_ID_LOG_PROBLEM_DETECTION@g" otel-demo-values.yaml

#############################################################################
# Create DT API secret for collector
kubectl create secret generic dynatrace-otelcol-dt-api-credentials \
  --from-literal=DT_ENDPOINT=$full_gen2_url/api/v2/otlp \
  --from-literal=DT_API_TOKEN=$DT_API_TOKEN_OBSLAB_LOG_PROBLEM_DETECTION

#############################################################################
# Install RBAC items so collector can talk to k8s API
# to retrieve topology info / pod metadata
kubectl apply -f collector-rbac.yaml

#############################################################################
# Install collector
helm upgrade -i dynatrace-collector open-telemetry/opentelemetry-collector -f collector-values.yaml

#############################################################################
# Install OpenTelemetry demo app
helm upgrade -i my-otel-demo open-telemetry/opentelemetry-demo -f otel-demo-values.yaml

#############################################################################
# Creation Ping
# curl -X POST https://grzxx1q7wd.execute-api.us-east-1.amazonaws.com/default/codespace-tracker \
#   -H "Content-Type: application/json" \
#   -d "{
#     \"repo\": \"$GITHUB_REPOSITORY\",
#     \"demo\": \"obslab-log-problem-detection\",
#     \"codespace.name\": \"$CODESPACE_NAME\"
#   }"
