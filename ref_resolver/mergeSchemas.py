import json, sys, os
from ref_resolver import RefResolver

path = os.path.abspath(sys.argv[1])
print path

# grab python dict from json schema files
json_obj = json.load(open(path))

# call to API resolve method
if 'id' in json_obj:
	RefResolver(json_obj['id'], path).resolve(json_obj)

file = open(path, "w")
file.write(json.dumps(json_obj, indent=4, sort_keys=True))
file.close()