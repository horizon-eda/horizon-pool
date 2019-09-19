import uuid
import sys, os
import json, requests, fcntl, time

self_path = os.path.dirname(os.path.abspath(__file__))
pool_path = os.getenv("HORIZON_POOL") or os.path.dirname(self_path)

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

class VendorSubBasepartMaker(object):
    def __init__(self, basepartdir, uuidgen):
        self.basepartdir = basepartdir
        self.uuidgen = uuidgen

        import sqlite3
        self.pooldb = sqlite3.connect(os.path.join(pool_path, 'pool.db'))
        cursor = self.pooldb.cursor()

        self.baseparts = []
        self.pkgs = {}
        self.uuids = {}

        self.cache = {}

        pdir = os.path.join(pool_path, 'parts', basepartdir)
        for fn in os.listdir(pdir):
            if fn.startswith('.') or not fn.endswith('.json'):
                continue
            with open(os.path.join(pdir, fn), 'r') as fd:
                part = json.load(fd)
                uuid = part['uuid']
                pkguuid = part['package']

                cursor.execute("SELECT uuid, name, filename FROM packages WHERE uuid = ?", [pkguuid])
                pkgs = cursor.fetchall()
                if len(pkgs) != 1:
                    raise ValueError('could not find package with uuid %s in pool' % pkguuid)

                pdata = {
                    'part': part,
                    'package': pkgs[0],
                }
                self.baseparts.append(pdata)
                self.pkgs.setdefault(pkgs[0][1], []).append(pdata)
                assert uuid not in self.uuids
                self.uuids[uuid] = pdata

    def get_pkg_base_uuid(self, pkg):
        if pkg not in self.pkgs:
            raise IndexError('no base part with package %s available' % pkg)
        assert len(self.pkgs[pkg]) == 1
        return self.pkgs[pkg][0]['part']['uuid']

    def find_or_make(self, vendordir, name, baseuuid, attrs = {}, filename = None):
        if name in self.cache:
            return self.cache[name]

        vendordir = os.path.join(pool_path, 'parts', self.basepartdir, vendordir)
        os.makedirs(vendordir, exist_ok = True)

        parent = self.uuids[baseuuid]['part']

        partdata = {
            "MPN": [False, name],
            "base": baseuuid,
            "type": "part",
            "uuid": str(self.uuidgen.get(name)),

            "inherit_model": True,
            "inherit_tags": True,
            "parametric": {},

            "tags": [],
        }
        # at the time of writing this, inheriting values across multiple
        # levels of base parts was buggy, so copy the values here.
        for inherit in ['datasheet', 'description', 'manufacturer', 'value']:
            if inherit in parent:
                partdata[inherit] = [True, parent[inherit][1]]

        partdata.update(attrs)

        with open(os.path.join(vendordir, filename or ('%s.json' % name)), 'w') as fd:
            json.dump(partdata, fd, sort_keys=True, indent=4)

        self.cache[name] = partdata['uuid']
        self.uuids[partdata['uuid']] = {
            'part': partdata,
            'package': self.uuids[baseuuid]['package'],
        }
        return partdata['uuid']

    def find_or_make_pkg(self, vendordir, name, basepkg, attrs = {}, filename = None):
        return self.find_or_make(vendordir, name, self.get_pkg_base_uuid(basepkg), attrs, filename)

class CachedURL(object):
    '''
    download and store a URL, or use previously downloaded data

    Instantiating the object does not trigger the download, this happens by
    calling the object (e.g. "obj = CachedURL('http://foo'); data = obj()").

    Unless overridden, the default location for the cache JSON file is next
    to where this python file is located, in a file called "urlcache.json".
    Updating this file is done using flock() as to not cause race issues when
    multiple scripts are executed in parallel.

    Note that since merging this file while handling git pull requests is
    probably a PITA so each of the various vendor downloader scripts should
    use its own file.
    '''

    # don't unnecessarily re-read cache file by keeping it in a class var
    _cache = None

    def __init__(self, url, cachefile = None):
        self._cachefile = cachefile or os.path.join(self_path, 'urlcache.json')
        self.url = url

    def __call__(self):
        if hasattr(self, '_data'):
            return self._data

        if CachedURL._cache is not None:
            cache = CachedURL._cache
        else:
            try:
                with open(self._cachefile, 'r') as cachefd:
                    cache = json.load(cachefd)
            except json.decoder.JSONDecodeError:
                cache = {}
            except FileNotFoundError:
                cache = {}

        iso8601 = '%Y-%m-%dT%H:%M:%SZ'

        def do_load(url):
            sys.stderr.write('fetching: %s\n' % url)
            start = time.time()

            r = requests.get(url)
            if r.status_code != 200:
                raise IOError('HTTP code %d on URL "%s"' % (r.status_code, url))

            sys.stderr.write('fetched:  %s (%d bytes in %f s)\n' % (url, len(r.text), time.time() - start))

            # need to re-read cache file with file locked in case another
            # process is also updating it.  LOCK_EX requires write access on
            # NFSv4 so open oldcachefd for writing even though we only read.
            with open(self._cachefile, 'a+') as oldcachefd:
                oldcachefd.seek(0)
                fcntl.flock(oldcachefd, fcntl.LOCK_EX)
                try:
                    cache = json.load(oldcachefd)
                except json.decoder.JSONDecodeError:
                    cache = {}

                cache[url] = {
                    'data': r.text,
                    'ts': time.strftime(iso8601, time.gmtime()),
                }

                with open(self._cachefile + '.tmp', 'w') as cachefd:
                    json.dump(cache, cachefd, sort_keys=True, indent=4)
                os.rename(self._cachefile + '.tmp', self._cachefile)
                CachedURL._cache = cache

            return r.text

        if self.url not in cache:
            self._data = do_load(self.url)
        else:
            # TBD: support redownloading after some time
            #ts = time.strptime(iso8601, cache[self.url]['ts'])
            self._data = cache[self.url]['data']

        return self._data

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
