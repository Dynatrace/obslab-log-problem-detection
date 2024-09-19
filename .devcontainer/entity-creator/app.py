import argparse
import sys
import json
import requests

# Usage
# API Token Permissions required: "read settings", "write settings", "ingest metrics"
#
# pip3 install requests
# Dry Run (No changes persisted)
# python3 app.py --input input.json --environment https://abc12345.live.dynatrace.com --token dtc01.*** --dry-run
# Real Run
# python3 app.py --input input.json --environment https://abc12345.live.dynatrace.com --token dtc01.***

PARSER = argparse.ArgumentParser()
DRY_RUN = False

def main():

    # If no args are provided, print help message and exit
    if len(sys.argv) == 1 and "app.py" in sys.argv:
        print("Usage: python app.py -h")
        exit()

    # Process incoming arguments
    PARSER.add_argument('--d','--dry-run',action='store_true') # action='store_true' is the magic that makes --d and --dry-run usable without any argument values
    PARSER.add_argument('--i','--input', help='Specify your input.json file. Defaults to input.json in the local folder.',default='input.json')
    PARSER.add_argument('--e','--environment', help='Dynatrace Environment URL: https://abc12345.live.dynatrace.com',required=True)
    PARSER.add_argument('--t','--token', help='Dynatrace API Token. dtc01.***', required=True)

    args = PARSER.parse_args()

    dry_run = args.d
    if dry_run:
        print('Dry Run Mode. Changes will not be persisted.')
        DRY_RUN = True

    input_file = args.i
    environment = args.e
    token = args.t

    ## Step 1: Read Input File and Build Entities
    incoming_entities = read_input_and_build_entities(input_file)

    # Only proceed if NOT in dry run mode
    if not dry_run:
        # Step 2: Check Existing Items In Dynatrace
        entity_names_to_create = check_entities_in_dynatrace(incoming_entities, environment, token)
        print(f">>>> Here are the items we will create: {entity_names_to_create}")

        print('>>>> Creating ' + str(len(entity_names_to_create)) + ' custom entities types')

        # Proactively exit if there are no entities to create
        if len(entity_names_to_create) == 0:
            exit()

        # Step 3: Create Entity Types in Dynatrace
        dt_entities = create_entity_types(incoming_entities, entity_names_to_create)

        # Step 4: Post to DT if NOT in dry run mode
        response = post_to_dt(dt_entities, environment=environment, token=token)

        print('')
        print('-- Step 4: Output --')
        print('')

        if response.status_code == 200:
            count = 0
            print("Your entity type(s) have been created:")
            print('')
            print('Get the entity type(s):')
            print(f'curl -X GET "{environment}/api/v2/settings/objects?schemaIds=builtin%3Amonitoredentities.generic.type&scopes=environment&fields=objectId%2Cvalue" -H "accept: application/json; charset=utf-8" -H "Authorization: Api-Token {token}"')
            print('')

            for entity in dt_entities: # This section simply builds helpful prebuild curl commands for you to use.
                count += 1
                
                print('=====================================================================')
                print(f"View {entity['value']['displayName']} entities:")
                print(f"{environment}/ui/entity/list/{entity['value']['name']}")
                print('')
                print("Try pushing some metrics (this will also create the entities):")
            
                curl_body = f"entity.{entity['value']['displayName']}.discovered,{entity['value']['displayName']}=SERVICE-NAME-HERE" # Use displayName not name as name is 'entity:sodacan' and displayName is what we need: 'sodacan'

                for rule in entity['value']['rules']:
                    for attribute in rule['attributes']:
                        curl_body += f",{attribute['key']}=yourValue"

                # Finally, append the " 1" metric to the discovered metric
                curl_body += " 1"
                
                print(f'curl -X POST "{environment}/api/v2/metrics/ingest" -H "accept: */*" -H "Authorization: Api-Token {token}" -H "Content-Type: text/plain; charset=utf-8" -d "{curl_body}"')
                print('')
        else:
            print('-------------------------------------------------')
            print("Error creating entities.")
            print(f"Response Code: {response.status_code}")
            print(response.text)
            print('-------------------------------------------------')
    else:
        print("Finished workflow. Script executed in --dry-run mode or there are no entities to create.")

def read_input_and_build_entities(input_file):
    print("-- Step 1: Read Input File and Build Entities --")

    try:
        entities = []
        file = open(input_file, "r")
        json_payload = json.load(file)

        for entity in json_payload:
            # For each entity, add two default metrics:
            # If entity name was 'sodacan' then add
            # 'sodacan.discovered' and 'sodacan'
            # The 'sodacan' metric must be unique for each sodacan
            entity['metrics'] = [ f"{entity['name']}.discovered" ]
            entity['metrics'].append(f"{entity['name']}")
            entities.append(entity)

        file.close() # Close file
    except:
        print('Exception caught. Does the file exist?')
        exit()

    return entities

def check_entities_in_dynatrace(entities, environment, token):
    print("-- Step 2: Check For Existing Entities in Dynatrace --")
    # Note: Only items NOT already present in Dynatrace will be created

    items_to_create = [] # A list of strings holding the 'name' values for items we WILL create (this is returned)
    # Start with a full list. Items found matching will be removed
    for entity_to_potentially_create in entities:
        items_to_create.append(entity_to_potentially_create['name'])

    headers = {
        "accept": "application/json",
        "authorization": f"Api-Token {token}"
    }

    endpoint = f"{environment}/api/v2/settings/objects?schemaIds=builtin%3Amonitoredentities.generic.type&scopes=environment&fields=objectId%2Cvalue"

    response = requests.get(url=endpoint, headers=headers)

    if response.status_code != 200:
        print(">>>> Cannot check existing objects in Dynatrace. Most likely a network error. Exiting.")
        exit()
    
    for existing_entity in response.json()['items']:
        if existing_entity['value']['displayName'] in items_to_create: # If a match is found to an existing item, do not create a second copy.
            items_to_create.remove(existing_entity['value']['displayName'])
            print(f">>>> Found an existing item for: {existing_entity['value']['displayName']}. Will not create.")
            
    return items_to_create

def create_entity_types(entities, entity_names_to_create):
    print('-- Step 3: Create Entity Types in Dynatrace --')
    
    dt_entities = [] # Master List

    for entity in entities:
        # if the entity name IS NOT in the list we should create, skip it
        if entity['name'] not in entity_names_to_create:
            print(f">>>> Skipping creation of {entity['name']}. It already exists in Dynatrace.")
            continue

        dt_entity = {
			"schemaId": "builtin:monitoredentities.generic.type",
			"scope": "environment",
            "value": {
                "enabled": True,
                "name": f"entity:{entity['name']}",
                "displayName": entity['name'],
                "createdBy": "Entity Creator Tool"
            }
		}

        # "Metrics" + "$prefix(entity.service)"   -  Y
        # "Events" + "$prefix(entity.service)"
        # "Logs"   - Y
        # "Spans"  - Y
        # "Business Events"   - Y
        
        
        dt_entity_sources = []
        dt_entities_metrics_entity_source = {
            "sourceType": "Metrics",
            "condition": f"$prefix(entity.{entity['name']})"
        }
        dt_entities_events_entity_source = {
            "sourceType": "Events",
            "condition": f"$prefix(entity.{entity['name']})"
        }
        # This doesn't need a condition
        # All incoming logs will be matched against {entity['name']}id (eg. carid)
        # So you just need to send the unique field in the log
        # For example:
        # { "carid": 1, "status": "INFO", "content": "log line entry here..." }
        dt_entities_logs_entity_source = {
            "sourceType": "Logs"
        }
        dt_entities_spans_entity_source = {
            "sourceType": "Spans"
        }
        dt_entities_business_events_entity_source = {
            "sourceType": "Business Events"
        }

        dt_entity_sources.append(dt_entities_metrics_entity_source)
        dt_entity_sources.append(dt_entities_events_entity_source)
        dt_entity_sources.append(dt_entities_logs_entity_source)
        dt_entity_sources.append(dt_entities_spans_entity_source)
        dt_entity_sources.append(dt_entities_business_events_entity_source)

        # Build Attributes
        # Loop through the entity attributes and build objects
        # The add objects to 
    
        dt_entity_attributes = []
        #for entity in entities:
        for attribute in entity['attributes']:
            dt_entity_attribute = {
                "key": attribute,
                "displayName": attribute,
                "pattern": "{" + attribute + "}"
            }
            dt_entity_attributes.append(dt_entity_attribute)

        # Build Required dimension (pulled from the attributes)
        dt_required_entity_dimension = {
            "key": f"{entity['name']}"
        }

        # Build Required Attributes List
        dt_entity_required_attributes = []
        dt_entity_required_attributes.append(dt_required_entity_dimension)

        # Build Rules
        dt_entity_rules = []
        entity_name = f"{entity['name']}" 
        dt_entity_rule = {
            "idPattern": "{" + entity_name + "}", # eg. {sodacan}
            "instanceNamePattern": "{" + entity_name + "}", # eg. {sodacan}
            "sources": dt_entity_sources,
            "attributes": dt_entity_attributes
        }
        dt_entity_rules.append(dt_entity_rule)

        # Attach rules to entity
        dt_entity['value']['rules'] = dt_entity_rules
    
        # Add entity to master list
        dt_entities.append(dt_entity)

    return dt_entities

def post_to_dt(dt_entities, environment, token):
    print("-- Step 4: Create Dynatrace Configurations (dry mode is disabled) --")

    headers = {
        "accept": "application/json",
        "authorization": f"Api-Token {token}"
    }

    endpoint = f"{environment}/api/v2/settings/objects"

    response = requests.post(url=endpoint, json=dt_entities, headers=headers)

    return response



if __name__ == "__main__":
    main()
