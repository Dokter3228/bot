import json

def read(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def write(file_path, user_info):
    with open(file_path, 'w') as file:
        json.dump(user_info, file, indent=4)