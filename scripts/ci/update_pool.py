import horizon

files = set()
error = False

def cb(st, filename, msg) :
	global error
	if st in (horizon.Pool.UPDATE_STATUS_ERROR, horizon.Pool.UPDATE_STATUS_FILE_ERROR) :
		print("ERROR", st, filename, msg)
		error = True
	if st == horizon.Pool.UPDATE_STATUS_FILE :
		files.add(filename)

print("updating pool...")
horizon.Pool.update(".", cb)
print("%d files "% len(files))

if error :
	exit(1)
