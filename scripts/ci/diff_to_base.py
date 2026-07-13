import pygit2
import sqlite3
import sys
base = sys.argv[1]

repo = pygit2.Repository(".")
conn = sqlite3.connect("pool.db")
cur = conn.cursor()


diff = repo.diff("HEAD", base)
for delta in diff.deltas :
	filename = delta.new_file.path
	cur.execute("SELECT type, name FROM all_items_view WHERE filename=?", (filename,))
	r = cur.fetchone()
	if r is not None :
		print("New %s '%s': %s"%(r[0], r[1], filename))
	else:
		print("::warning file=%s::Not found in pool"%filename)
