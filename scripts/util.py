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

prefixes = {
	-15 : "f",
	-12 : "p",
	 -9 : "n",
	 -6 : "µ",
	 -3 : "m",
	  0 : "",
	  3 : "k",
	  6 : "M",
	  9 : "G",
	 12 : "T",
}

reversepfx = dict([(v, k) for k, v in prefixes.items()])
reversepfx['u'] = -6

def format_si(value, digits, strip=True) :
	v = abs(value)
	exp = 0
	while v >= 1e3 and exp <= 12 :
		v /= 1e3
		exp += 3
	if v > 1e-15 :
		while v < 1 and exp >= -12 :
			v *= 1e3
			exp -= 3
	if value < 0 :
		s = "-"
	else :
		s = ""
	n = ("%." + str(digits) + "f")%v
	if strip :
		n = n.rstrip("0").rstrip(".")
	s+= n + " " + prefixes[exp]
	return s

def parse_si(value):
    value = value.strip()
    if value[-1] in reversepfx:
        return float(value[:-1]) * 10 ** reversepfx[value[-1]]
    else:
        return float(value)
