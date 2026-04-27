import requests
from dotenv import load_dotenv
import os

load_dotenv()

DT_URL = os.environ.get("DT_URL", "")
DT_API_TOKEN = os.environ.get("DT_API_TOKEN", "")
DT_ENDPOINT = f"{DT_URL}/api/v2/events/ingest"

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "accept": "application/json; charset=utf-8",
    "Authorization": f"Api-Token {DT_API_TOKEN}"
}
payload = {
    "title": "feature flag changed",
    "entitySelector": "type(SERVICE),entityName.equals(cart)",
    "eventType": "CUSTOM_CONFIGURATION",
    "properties": {
      "dt.event.is_rootcause_relevant": True,
      "action": "changed",
      "feature_flag.key": "cartFailure",
      "defaultValue": "on"
    }
}

resp = requests.post(
    url=DT_ENDPOINT,
    headers=headers,
    json=payload
)

print(resp.status_code)