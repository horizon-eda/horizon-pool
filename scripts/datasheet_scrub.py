import sqlite3
import requests

con = sqlite3.connect('pool.db')
cur = con.cursor()

fails = []
headers={'user-agent': 'Mozilla/5.0'}

for ds, MPNs in cur.execute("SELECT datasheet, group_concat(MPN, ', ') from parts where datasheet != '' group by datasheet"):
    #ds = row[0]
    try :
        r=requests.head(ds, allow_redirects=True, timeout=10, headers=headers)
        r.raise_for_status()
        print("OKAY ", ds)
    except requests.exceptions.RequestException:
        print("RETRY GET", ds)
        try :
            r=requests.get(ds, allow_redirects=True, timeout=10, headers=headers)
            r.raise_for_status()
            print("OKAY ", ds)
        except requests.exceptions.RequestException as e:           
            print("ERR", ds, e)
            fails.append((ds, MPNs, e))

print(fails)