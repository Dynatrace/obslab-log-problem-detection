#!/bin/bash
# Usage: ./runtimeChange.sh serviceName flagKey newFlagValue
# eg. ./runtimeChange.sh cartservice cartServiceFailure on

echo "Changing feature flag key: $2 to $3 for service: $1"

##############
# Step 1
# Inform Dynatrace that a configuration change is occurring
##############
curl -X POST "$DT_URL_OBSLAB_LOG_PROBLEM_DETECTION/api/v2/events/ingest" \
  -H "accept: application/json; charset=utf-8" -H "Authorization: Api-Token $DT_API_TOKEN_OBSLAB_LOG_PROBLEM_DETECTION" -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"title\": \"feature flag changed\",
    \"entitySelector\": \"type(entity:service),entityName.equals($1)\",
    \"eventType\": \"CUSTOM_CONFIGURATION\",
    \"properties\": {
      \"dt.event.is_rootcause_relevant\": true,
      \"action\": \"changed\",
      \"service\": \"$1\",
      \"feature_flag.key\": \"$2\",
      \"defaultValue\": \"$3\"
    }
  }"

# TODO
#{
#  "eventType": "CUSTOM_DEPLOYMENT",
#  "title": "Easytravel 1.1",
#  "entitySelector": "type(PROCESS_GROUP_INSTANCE),tag(easytravel)",
#  "properties": {
#    "dt.event.deployment.name":"Easytravel 1.1",
#    "dt.event.deployment.version": "1.1",                  <-- Mandatory
#    "dt.event.deployment.release_stage": "production" ,
#    "dt.event.deployment.release_product": "frontend",
#    "dt.event.deployment.release_build_version": "123",
#    "approver": "Jason Miller",
#    "dt.event.deployment.ci_back_link": "https://pipelines/easytravel/123",
#    "gitcommit": "e5a6baac7eb",
#    "change-request": "CR-42",
#    "dt.event.deployment.remediation_action_link": "https://url.com",
#    "dt.event.is_rootcause_relevant": true
#  }
#}

##############
# Step 2
# Change the $2 feature flag key to the value of $3
# This is messy (and in reality would be handled with a proper GitOps process eg. Pull Requests and a tool like ArgoCD)
# 1. Read flags.yaml with yq
# 2. Get the JSON flag values from .data and pass to jq
# 3. jq changes the defaultValue
# 4. This is saved as an environment variable RESULT
# 5. Add a pipe and newline to result and use yq to edit flags.yaml inplace
# 6. kubectl apply the changed file
##############
RESULT=$(yq '.data["demo.flagd.json"]' .devcontainer/otel-demo/flags.yaml | yq ".flags.$2.defaultVariant = \"$3\"")
res=$RESULT yq -i '.data["demo.flagd.json"] = env(res)' .devcontainer/otel-demo/flags.yaml
sed -i 's/  demo.flagd.json: /  demo.flagd.json: |\n    /g' .devcontainer/otel-demo/flags.yaml

# Apply changes
kubectl apply -f .devcontainer/otel-demo/flags.yaml

echo "service: $1 flag: $2 property: defaultVariant set to value: $3"
