import subprocess
from urllib.parse import urlparse, parse_qs

def extract_endpoints_and_params(input_file, endpoints_file, params_file, seen_params):
    with open(input_file, 'r') as infile, \
         open(endpoints_file, 'a') as endpoint_outfile, \
         open(params_file, 'a') as params_outfile:
        
        for line in infile:
            line = line.strip()
            if line:
                parsed_url = urlparse(line)
                endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                params = parse_qs(parsed_url.query)

                endpoint_outfile.write(endpoint + '\n')

                if params:
                    for key in params.keys():
                        if key not in seen_params:
                            params_outfile.write(f"{key}\n")
                            seen_params.add(key)

    return

def run():
    input_file_archive = 'temp/archive_list.txt'
    input_file_spider = 'temp/spider_list.txt'
    endpoints_file = 'temp/endpoints_tmp.txt'
    endpoints_archive = 'temp/endpoints_archive.txt'
    params_file = 'temp/params_final.txt'
    seen_params = set()

    #Clear the old content of it
    with open(params_file, 'w') as filex:
        pass
    with open(endpoints_file, 'w') as filey:
        pass
    with open(endpoints_archive, 'w') as filez:
        pass

    extract_endpoints_and_params(input_file_archive, endpoints_archive , params_file, seen_params)
    extract_endpoints_and_params(input_file_spider, endpoints_file, params_file, seen_params)
    return


