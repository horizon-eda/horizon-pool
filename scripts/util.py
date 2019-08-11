import uuid
import os

class UUIDGenerator:
	def __init__(self, filename) :
		self.filename = filename
		if os.path.isfile(filename) :
			with open(filename, "r") as fi :
				self.uuids = {k:uuid.UUID(v) for k,v in (l.strip().split("\t") for l in fi.readlines() if len (l.strip()))}
		else :
			self.uuids = {}
		
	def get(self, key) :
		if key in self.uuids :
			return self.uuids[key]
		else :
			uu = uuid.uuid4()
			with open(self.filename, "a") as fi :
				fi.write(key + "\t" + str(uu) + "\n")
			self.uuids[key] = uu
		return uu
