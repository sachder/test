import time
import requests
import pprint
import os
import sqlite3
from requests.packages.urllib3.exceptions import *
from multiprocessing import Pool

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Basic configuration and database connectivity
CURRENT_CATEGORY = "Action"

packages_dir = "packages/"
db = sqlite3.connect("apkinfo.db")
apks_dir = "apks/"
PACKAGE, NAME, RATING, CATEGORY, LAST_UPDATED, VERSION, DOWNLOAD_LINK = 0, 1, 2, 3, 4, 5, 6

print "[*] Database setup complete"
print "[*] Reading applications from database"

applications = db.execute('SELECT * FROM APP WHERE CATEGORY NOT IN ("' + CURRENT_CATEGORY + '")').fetchall();

print "[*] Found {} applications".format(len(applications))

def download_and_save(app):
    TIME_DELAY = 30
    print "[#] Trying to download {}".format(app[PACKAGE])
    save_path = str(apks_dir) + str(app[CATEGORY]) + "/"
    try:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
    except Exception as e:
        # Another thread probably made the directory before another one - ignore the race condition
        pass

    retry_path = save_path + "retry_log"
    save_path = save_path + str(app[PACKAGE]) + ".apk"
    if os.path.isfile(save_path):
        print "[~] Skipping {}, apk already downloaded".format(app[PACKAGE])
        return "[~] Skipped downloading " + str(app[PACKAGE]) + ", apk already downloaded"
    try:
        r = requests.get(app[DOWNLOAD_LINK], allow_redirects=True)
        if r.status_code == 200:
            open(save_path, 'wb').write(r.content)
            print "[+] Downloaded and saved {}".format(app[PACKAGE])
        else:
            raise Exception("Failed to get a valid status code to file, got: " + str(r.status_code) + ", response: " + str(r.content))
    except Exception as e:
        print "[-] Got exception: {}".format(e)
        print "[x] Failed to download {}".format(app[PACKAGE])
        with open(retry_path, 'a') as f:
            f.write(app[PACKAGE] + "\n")
        time.sleep(TIME_DELAY)
        return "[x] Failed to download {}".format(app[PACKAGE])

    time.sleep(TIME_DELAY)
    return "[+] Downloaded and saved {}".format(app[PACKAGE])


if __name__ == '__main__':
    pool = Pool(processes=6)
    results = pool.map(download_and_save, applications)
    pool.close()
    pool.join()

    print "\n\nFinal output:"
    print "------------------------------------------------------\n\n"
    pprint.pprint(results)
    exit()
