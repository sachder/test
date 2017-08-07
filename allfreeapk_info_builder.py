from bs4 import BeautifulSoup
import requests
import pprint
import os
import sqlite3
from requests.packages.urllib3.exceptions import *
from multiprocessing import Pool

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Basic configuration and database connectivity
html_dir = "temp_htmls/"
db = sqlite3.connect("apkinfo.db")
allfreeapk_url = "https://www.allfreeapk.com/search.php?q="


print "[*] Database setup complete"

malwares = db.execute("SELECT MD5, PACKAGE FROM MALWARES").fetchall()


def get_app_info(malware):
    md5, package_name = malware

    full_url = allfreeapk_url + package_name
    print "[#] Getting information for package {}".format(package_name)
    print "\t[-] Requesting URL {}".format(full_url)
    search_page = requests.get(full_url, verify=False)

    save_path = os.path.join(html_dir, package_name + "-" + md5)
    if os.path.isfile(save_path):
        print "[~] Skipping {}, apk info already downloaded".format(package_name)
        return "[~] Skipped downloading " + str(package_name) + ", apk already downloaded"

    with open(save_path, 'a')as f:
        f.write(search_page.content)

    return "\t[+] Downloaded info for {}".format(package_name)


if __name__ == '__main__':
    pool = Pool(processes=5)
    results = pool.map(get_app_info, malwares)
    pool.close()
    pool.join()

    print "\n\nFinal output:"
    print "Total malwares: {}, Processed: {}".format(len(malwares), len(results))
    print "------------------------------------------------------\n\n"
    pprint.pprint(results)
    exit(0)
