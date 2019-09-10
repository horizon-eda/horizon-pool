import sys
import uuid
import json

for filename in sys.argv[1:] :
	with open(filename, "r") as fi:
		j = json.load(fi)
	j['uuid'] = str(uuid.uuid4())
	#j['manufacturer'] = [False, "TDK"]
	with open(filename, "w") as fi:
		json.dump(j, fi, sort_keys=True, indent=4)
