#!/usr/bin/env python3

import os
import subprocess
import json
from urllib.parse import urlparse
import re
from utils.smashdupes import smashDupes

THREADS = 30
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
BLACKLIST_URLS = ["css", "jpeg", "png", "jpg", "gif", "svg" ,"bmp", "tif", "mp3", "wav", "ogg", "mp4", "avi", "mov", 
                  "pdf", "docx", "xlsx", "pptx","ico",
                  "woff", "woff2", "ttf"]

def removeFile(filename):
    os.remove(filename)

def extractDomainName(url):
    pattern = r'(https?://)?([a-zA-Z0-9-]+\.)*([a-zA-Z0-9-]+\.[a-zA-Z]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(3)
    else:
        return None

### SUBDOMAIN ###
def subfinder(url, includeSubdomain, subsFile_Tmp):

    if not includeSubdomain:
        print("[-] Skipping Subdomain Enumeration")
        with open(subsFile_Tmp,"w") as subdomainFile:
            subdomainFile.write(url)
        return

    print("[-] Performing Subdomain Enumeration")
    command = ["subfinder","-d", DOMAIN_NAME, "-o", subsFile_Tmp]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    # print(f"|--> Subdomain Enumeration saved to {subsFile_Tmp}")


def httpx_subdomains(subdomainsFile_Tmp, subdomainsFile):
    print(f"[-] Performing Httpx Probing")
    command = ["httpx", "-l" , subdomainsFile_Tmp, "-o", subdomainsFile]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    # print(f"|--> Httpx Probing saved To: {subdomainsFile}")


def getSubdomains(url,includeSubdomain):
    subdomainsFile = "Subdomains.txt"
    subdomainsFile_Tmp = f"{subdomainsFile}_tmp"
    subfinder(url, includeSubdomain, subdomainsFile_Tmp)
    httpx_subdomains(subdomainsFile_Tmp, subdomainsFile)

    removeFile(subdomainsFile_Tmp)
    return subdomainsFile


### URLS ###
def hakrawler(subdomainFile, header, proxy, urlsFile):
    urlsFile_Tmp = f"{urlsFile}_Tmp"
    
    print("[-] Running Hakrawler")

    #Katana
    command = f"katana -list {subdomainFile}"

    #Hakrawler
    # command = ["cat", subdomainFile, "|" , "hakrawler", "-u", "-t", str(THREADS), "-insecure", "-i"]  #Can't use list as shell is required due to bash
    # command = f"cat {subdomainFile} | hakrawler -u -t {THREADS} -insecure -i "                          #-u = unique | -i=InsideUrls (Need to see if required or not)

    if header:
        command += f' -H "{header}"'
    if proxy:
        command += f' -proxy "{proxy}"'

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    print(command)
    urlList, _ = process.communicate()

    with open(urlsFile_Tmp, "w") as urlFile:
        urlFile.write(urlList.decode('utf-8'))

    removeDupsCmd = ["grep", f"{DOMAIN_NAME}", urlsFile_Tmp, "|", "sort", "-u", ">>", urlsFile]   #Bash is fastest for this
    removeDupsCmd = " ".join(removeDupsCmd)
    process = subprocess.Popen(removeDupsCmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True).communicate()  #Saves to URL_FILENAME
    # uniqueURLs = list(set(urlList.decode()))


def goSpider(subdomainFile, header, proxy, urlsFile):
    print("[-] Running GoSpider")

    urlsFile_Tmp = f"{urlsFile}_Tmp"

    command = ["gospider", "-q", "-S", subdomainFile, "--length", "--depth", "1", "-t", str(THREADS), "--json", "-u", USER_AGENT]
    if header:
        command.extend(["-H", header])
    
    if proxy:
        command.extend(["-p]", proxy])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    urlListJson, _ = process.communicate()
    urlList = parseGoSpiderOutput(urlListJson.decode('utf-8'))

    finalUrls = "\n".join(urlList)                 #Fastest way
    with open(urlsFile_Tmp, "w") as urlFile:
        urlFile.write(finalUrls)

    removeDupsCmd = ["grep", f"{DOMAIN_NAME}", urlsFile_Tmp, "|",  "sort", "-u", ">>", urlsFile]  #Bash is fastest for this
    removeDupsCmd = " ".join(removeDupsCmd)
    process = subprocess.Popen(removeDupsCmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True).communicate()  #Saves to urlFilename

    #--blacklist <regex>: This flag exist, we will add if needed later


def gau(subdomainFile, header, proxy, urlsFile):
    print("[-] Running Get All URLs")

    THREADS = 5
    urlsFile_Tmp = f"{urlsFile}_Tmp"

    command = ["cat", subdomainFile, "|", "gau", "--threads", str(THREADS), "--o", urlsFile_Tmp]
    if proxy:
        command.extend(["--proxy", proxy])
    command = " ".join(command)

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True).communicate()

    removeDupsCmd = ["grep", f"{DOMAIN_NAME}", urlsFile_Tmp, "|",  "sort", "-u", ">>", urlsFile]  #Bash is fastest for this
    removeDupsCmd = " ".join(removeDupsCmd)
    process = subprocess.Popen(removeDupsCmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True).communicate()  #Saves to urlFilename



def parseGoSpiderOutput(urlListJson):
    urlList = set()
    for line in urlListJson.splitlines():
        try:
            urlJson = json.loads(line)
            finalUrl = urlJson["output"]
            urlList.add(finalUrl)
        except json.JSONDecodeError:
            pass

    return list(urlList)



def processCrawledURLs(urlsFile, filteredUrlsFile):
    filteredUrlsFile_Tmp = f"{filteredUrlsFile}_Tmp"
    
    #URLLess
    command = ["urless", "-i", urlsFile, "-o", filteredUrlsFile_Tmp]   

    #URO
    # command = ["uro", "-i", urlsFile, "-o", filteredUrlsFile_Tmp]      //URLess is better

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).communicate()
    print("[-] Processed Crawled URLs using uro")

    #Remove Blacklisted Extensions  (uro filters most of the URLs)
    filteredUrlsFile_Tmp2 = f"{filteredUrlsFile}_Tmp2"
    blacklistStr = '|'.join(BLACKLIST_URLS)
    grep_command = f"grep -v -E '\\.({blacklistStr})$' {filteredUrlsFile_Tmp} > {filteredUrlsFile_Tmp2}"
    process = subprocess.Popen(grep_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,shell=True).communicate()
    print("[-] Removed Blacklisted URLs")
 
    #Filter404 URLs
    print(f"[-] Filtering 404 Urls")
    command = ["httpx", "-l" , filteredUrlsFile_Tmp2, "-fc", "404", "-o", filteredUrlsFile]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).communicate()
    removeFile(filteredUrlsFile_Tmp)
    removeFile(filteredUrlsFile_Tmp2)


def LinkFinder(JsFolderPath, linkFinderFile="Linkfinder_urls.txt"):     #Fetch Links from JS files
    print("[-] Extracting URLS from JS Files using LinkFinder")
    command = f"linkfinder.py -i '{JsFolderPath}/*' -o cli | sort -u > {linkFinderFile}"
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True).communicate()
    Process_LinkfinderOutput


def Process_LinkfinderOutput(linkFinderFile):
    print("[-] Processing LinkFinder Output")
    linkFinderFile_Tmp = f"{linkFinderFile}_Tmp"
    
    #Todo: File Contains /api/v2 (relativeURL)  |  http://manydomains.com (absolutePath) | text/xml (contentTypes as well)
           #In which domain to append these relativeURLs?  || Write Blacklist filter to remove these contentTypes
    pass

    removeFile(linkFinderFile_Tmp)


def crawlURLs(subdomainFile, header, proxy):
    urlsFile = "URL_List.txt"
    urlsFile_Tmp = f"{urlsFile}_Tmp"
    
    hakrawler(subdomainFile, header, proxy, urlsFile)
    goSpider(subdomainFile, header, proxy,  urlsFile)
    gau(subdomainFile, header, proxy,  urlsFile)

    filteredUrlsFile = "Unique_URL_List.txt"
    processCrawledURLs(urlsFile,filteredUrlsFile)
    
    print(f"[-] Crawled URLs saved: {filteredUrlsFile}")
    removeFile(urlsFile_Tmp)
    return filteredUrlsFile


###JAVASCRIPT

def subjs(crawledFile, subjsFile):
    print("[-] Extracting JS URLs from Crawled URLs")
    command = f"cat {crawledFile} | subjs | grep {DOMAIN_NAME}"
    subjsUrls, _ = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True).communicate()
    subjsUrlsList = list(set(subjsUrls.decode().splitlines()))  #Remove Dups

    subjsURLsFinal = "\n".join(subjsUrlsList)
    with open(subjsFile, "w") as jsfw:
        jsfw.write(subjsURLsFinal)
    print(f"[-] JS URLs saved: {subjsFile}")




def downloadJSFiles(subjsFile, jsFolderPath):
    print("[-] Downloading JS Files locally from JS URLs")
    cmdJsDownload = f"aria2c -c -x 10 -d {jsFolderPath} -i {subjsFile}"

    output, _ = subprocess.Popen(cmdJsDownload, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True).communicate()
    print(("[-] Javascript Files Download Completed"))


    ###TODO: INSTEAD OF THIS WRITE TOOL FOR SMASH DUPES HERE ONLY AS NEW FILE
    count = smashDupes(jsFolderPath)
    print(f"[+] Removed Duplicate Javascript Files: {count}")


def processJSUrls(subjsFile, subjsFile_Tmp):
    pass


def jsRecon(crawledFile):
    subjsFile = "JSUrls.txt"
    # subjsFile_Tmp = f"{subjsFile}_Tmp"
    subjs(crawledFile, subjsFile)

    #If no JS Files were Found
    if os.path.getsize(subjsFile) == 0:
        print("[-] No JS Files Found")
        return

    #If JS Files were Found
    jsFolderPath = "JS_Files"
    downloadJSFiles(subjsFile, jsFolderPath)
    return jsFolderPath


# def getParamsFromCrawledURLs(crawledFile, paramsWordlistFilename):
#     print("[-] Extracting Parameters from Crawled URLs")
#     command = f"cat {crawledFile} | unfurl --unique keys"
#     paramsListTmp, _ = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True).communicate()

#     paramsList = "\n".join(paramsListTmp.decode().splitlines())
#     with open(paramsWordlistFilename, "a") as paramsFile:
#         paramsFile.write(paramsList)

### PARAM ###
def getParamsFromCrawledURLs(crawledFile, paramsWordlistFilename):
    from urllib.parse import urlparse, parse_qs

    paramsList = set()  
    
    with open(crawledFile, 'r') as file:
        for url in file:
            parsed_url = urlparse(url.strip())
            query_params = parse_qs(parsed_url.query)      #Get Params
            paramsList.update(query_params.keys())         #Add ParamKeys to Set
    
    paramsList = "\n".join(paramsList)
    with open(paramsWordlistFilename, "a") as paramsFile:
        paramsFile.write(paramsList)



def buildParamWordlist(crawledFile):
    paramsWordlistFilename = "ParamsWordlist.txt"
    getParamsFromCrawledURLs(crawledFile, paramsWordlistFilename)
    return paramsWordlistFilename


def startscan(url,proxy=None,headers=None,includeSubdomain=True):
    global DOMAIN_NAME

    #INPUTS
    # header = "COOKIE: JSESSIONID=noob"
    # proxy = None                          #Format: 127.0.0.1:8080
    # includeSubdomain = True               #Add a button in UI that turns this on/off
    # url = "https://www.cafecoffeeday.com/"
    # url = "http://dhan.co/"
    # url = "http://testphp.vulnweb.com"

    DOMAIN_NAME = extractDomainName(url)

    #Tmp
    os.mkdir("results")
    os.chdir("results")
    
    subdomainFile = getSubdomains(url,True)
    crawledFile = crawlURLs(subdomainFile, header, proxy)
    jsFolderPath = jsRecon(crawledFile)
    paramsWordlistFile = buildParamWordlist(crawledFile)

    #TODO: Use LinkFinder | ProcessFiles | Get Parameters.
    #LinkFinder | GF | 


def main():
    startscan()    


if __name__=="__main__":
    main()


'''
TOOLS INSTALL
-------------
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/jaeles-project/gospider@latest
go install github.com/hakluke/hakrawler@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
pip3 install uro
sudo apt install -y aria2

LinkFinder --> git clone https://github.com/GerbenJavado/LinkFinder.git && cd LinkFinder && python3 setup.py install && 
               sed -i 's|^#!/usr/bin/env python$|#!/usr/bin/env python3|' linkfinder.py && ln -s $PWD/linkfinder.py /usr/local/bin

               
TODO
----
0)Replace Hakrwaler with Katana

1)Processing LinkFinder URL --> Check the function wrote usecases

WORDLISTS
1)https://github.com/s0md3v/Arjun/tree/master/arjun/db
2)https://github.com/PortSwigger/param-miner/blob/master/resources/params


DB Params
--> Frame the entire params as one request and check for reflection (10 params each req?)  
    a)The param value will be same as param same, so we know the reflected value (Not feasible for generic params like id)
    b)Create a mapping with random UUID for each param.

Hardcoded Secrets
https://github.com/m4ll0k/SecretFinder
'''