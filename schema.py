import json        
from urllib.parse import urlparse
from urllib.parse import parse_qs

def process_result(auth_header,auth_token):
    json_output = {"output": []}
    with open("temp/results_aux.txt", 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) >= 2:
                url = parts[1]
                status_code = str(parts[0])
                #status_code = status_code.strip('[]')
                raw_url = url.rstrip("/")
                param_dict = {}
    
                with open("temp/params_final.txt", 'r') as infile:
                    for line in infile:
                        param = line.strip()
                        if param:  # Skip empty lines
                            param_dict[param] = "test"
                
                out_final = {"status-code": status_code, "url": raw_url, "rawurl": raw_url, "httpMethod":"get", "headers": {auth_header:auth_token},  "queryParams": param_dict,"requestBody": {}}
                json_output["output"].append(out_final)
    # Write the processed data to a JSON file
    json_file = 'temp/output.json'
    with open(json_file, 'w') as file:
        json.dump(json_output, file, indent=4)  

    return json_output