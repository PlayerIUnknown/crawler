import os
import hashlib
from collections import defaultdict

def getHash(fileName):
	with open(fileName, "r") as f:
		fileHash = hashlib.blake2b()
		chunk = f.read(8192)
		while chunk:
			fileHash.update(chunk.encode())
			chunk = f.read(8192)
	return fileHash.hexdigest()


def smashDupes(directory):
	currentDir = os.getcwd()
	if directory:
		os.chdir(directory)
	allFiles = os.listdir()
	dicts=defaultdict(list)

	for file in allFiles:		  					 #Removing Directories
		if os.path.isdir(file):
			allFiles.remove(file)

	for file in allFiles:
		hashx = getHash(file)
		dicts[hashx].append(file)

	count = 0
	for duplicateList in dicts.values():
		for file in duplicateList[1:]:
			count +=1
			try:
				os.remove(file)
				# print(f"[-] Deleted File --> {file}")
			except Exception:
				print("[-] Error Deleting File --> {file}")

	#print(colored("\n[Complete]","cyan")+colored(f" Total Files Deleted = {count}","green"))
	os.chdir(currentDir)
	return count


#smashdupes("testDir")