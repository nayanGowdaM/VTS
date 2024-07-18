import json

# Function to convert JSONB array data to a list of dictionaries
def convert_jsonb_to_list(jsonb_array_data):
    json_data = json.loads(json.dumps(jsonb_array_data))
    return json_data


