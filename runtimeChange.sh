#!/bin/bash
# Usage: ./runtimeChange.sh serviceName flagKey newFlagValue
# eg. ./runtimeChange.sh my-otel-demo-cartservice cartServiceFailure on

echo "Changing feature flag key: $2 to $3 for service: $1"

##############
# Step 1
# Inform Dynatrace that a configuration change is occurring
##############
curl -X POST "$DT_URL_OBSLAB_LOG_PROBLEM_DETECTION/api/v2/events/ingest" \
  -H "accept: application/json; charset=utf-8" -H "Authorization: Api-Token $DT_API_TOKEN_OBSLAB_LOG_PROBLEM_DETECTION" -H "Content-Type: application/json; charset=utf-8" \
  -d "{
    \"title\": \"feature flag changed\",
    \"entitySelector\": \"type(SERVICE),entityName.equals($1)\",
    \"eventType\": \"CUSTOM_CONFIGURATION\",
    \"properties\": {
      \"dt.event.is_rootcause_relevant\": true,
      \"action\": \"changed\",
      \"feature_flag.key\": \"$2\",
      \"defaultValue\": \"$3\"
    }
  }"

echo
echo "Now manually change cartServiceFailure.defaultValue to on in flags.yaml and apply using kubectl"