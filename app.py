from flask import Flask, request, jsonify
import subprocess
import separator
import schema
import uuid
import os
import json
from utils.smashdupes import smashDupes


app = Flask(__name__)

@app.route('/spider', methods=['POST'])
def spider():
    # Parse JSON input
    data = request.get_json()
    url = data.get('url')
    auth_header = data.get('Auth-Header')
    auth_token = data.get('Auth-Token')
    includeSubs = data.get('includeSubs')

    # Validate input
    if not url or not auth_header or not auth_token:
        return jsonify({'error': 'Missing required parameters'}), 400

	#Subdomain Yes/No
    if includeSubs == "yes":
        print("[-] Performing Subdomain Enumeration")
        
		#Clear the old content of it
        with open("temp/list_subs.txt", 'w') as file:
            pass
        
        subs_command = ['subfinder', '-d', url, '-o', 'temp/list_subs.txt']
        subprocess.Popen(subs_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
        with open("temp/list_subs.txt", "a") as subs_file:
            subs_file.write(url)
        print("[+] Completed Subdomain Enumeration")
    else:
        print("[-] Skipping Subdomain Enumeration")
        with open("temp/list_subs.txt", "w") as subs_file:
            subs_file.write(url)
          
	# Probing list_subs.txt (with/without subs included)

    print("[-] Starting Httpx Probing")
    probe_command = ['httpx','-l','temp/list_subs.txt','-o','temp/final_subs.txt']
    subprocess.Popen(probe_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    print("[+] Completed Httpx Probing")

	#Spidering + Archive Mining Begins
    #Clear the old content of it
    with open("temp/archive_list.txt", 'w') as file:
        pass

    print("[-] Starting Archive Mining")
    #archive_command = ['cat','temp/final_subs.txt','|','gau','--o','temp/archive_list.txt']
    archive_command = "cat temp/final_subs.txt | gau --o temp/archive_list.txt"
    subprocess.run(archive_command, shell=True, check=True)
    #subprocess.Popen(archive_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    print("[+] Completed Archive Mining")

    print("[-] Starting Spidering")
    spider_command = ['katana','-list','temp/final_subs.txt','-H',f'{auth_header}:{auth_token}','-ct','100','-o','temp/spider_list.txt']
    subprocess.Popen(spider_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    print("[+] Completed Spidering")

    #Concatenates Output
    #subprocess.Popen("cat temp/archive_list.txt temp/spider_list.txt > temp/archive_spider_all.txt", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()

    #Separates URLs into endpoints and params
    print("[-] Running Separator")
    separator.run()
    print("[+] Executed Separator Successfully")
    print("[+] Parameters Deduplicated")

    #Declutters and Deduplicates Endpoint
    declutter_command = ['urless','-i','temp/endpoints_tmp.txt','-o','temp/endpoints_final.txt']
    print("[-] Declutteringing and Deduplicating Endpoints")
    subprocess.Popen(declutter_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    print("[-] Decluttered and Deduplicated Endpoints")

    # Probe all unique decluttered endpoints

    print("[-] Probing all endpoints")
    #validator_command = ['httpx','-list','temp/endpoints_final.txt','-t','150','-sc','-nc','-o','temp/results_aux.txt']
    #validator_command = ['cat', 'temp/endpoints_final.txt','|','hakcheckurl','>','temp/results_aux.txt']
    #subprocess.Popen(validator_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    validator_command = "cat temp/endpoints_final.txt | hakcheckurl > temp/results_aux.txt"
    subprocess.run(validator_command, shell=True, check=True)
    
    print("[+] Probing endpoints completed")

    print("[-] Curating the Schema")

    json_out = schema.process_result(auth_header,auth_token)
    
    scan_uuid = str(uuid.uuid4())
    scan_store = []
    scan_store.append(scan_uuid)
    if not os.path.exists('scan'):
        os.makedirs('scan')
    
    scan_file_path = os.path.join('scan', f'{scan_uuid}.json')

    # Write the scan data to the JSON file
    with open(scan_file_path, 'w') as json_file:
        json.dump(json_out, json_file, indent=4)

    return jsonify(json_out)

@app.route('/jsmine', methods=['GET'])
def jsmine():
    #js_command = "cat temp/endpoints_final.txt | grep .js > temp/js-urls.txt"
    #subprocess.run(js_command, shell=True, check=True)
    
    try:
        result = subprocess.run(
            "cat temp/endpoints_final.txt | grep .js > temp/js-urls.txt",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return {"Status":"No JS URLs found"}
        else:
            return {"Error occurred": {e.stderr.decode()}}


    print("[-] Downloading JS Files locally from JS URLs")
    cmdJsDownload = f"aria2c -c -x 10 -d js-file -i temp/js-urls.txt"
    subprocess.Popen(cmdJsDownload, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True).communicate()
    print(("[-] Javascript Files Download Completed"))

    count = smashDupes("js-file")
    print(f"[+] Removed Duplicate Javascript Files: {count}")

    # Integrate gf 007
    gf_command = "python3 utils/gf.py -a"
    subprocess.run(gf_command, shell=True, check=True)


    return {"Status":"Complete"}




    # command = f"echo 'URL: {url}, {auth_header}: {auth_value}'"
    # try:
    #     # Run the command
    #     result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     output = result.stdout.decode('utf-8')
    #     return jsonify({'output': output})
    # except subprocess.CalledProcessError as e:
    #     return jsonify({'error': str(e), 'stderr': e.stderr.decode('utf-8')}), 500

if __name__ == '__main__':
    app.run(debug=True)
