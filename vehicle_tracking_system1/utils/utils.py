import json

# Function to convert JSONB array data to a list of dictionaries
def convert_jsonb_to_list(jsonb_array_data):
    json_data = json.loads(json.dumps(jsonb_array_data))
    return json_data



def auth( username, password):
    if( username=='admin' and password=='admin'):
        return True
    return False