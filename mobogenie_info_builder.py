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
mobogenie_url = "https://m.mobogenie.com/search/?type=appgame&q="


print "[*] Database setup complete"

malwares = db.execute("SELECT MD5, PACKAGE FROM MALWARES WHERE LAST_UPDATED = 'last-updated'").fetchall()


def get_app_info(malware):
    md5, package_name = malware

    full_url = mobogenie_url + package_name
    print "[#] Getting information for package {}".format(package_name)
    #print "\t[-] Requesting URL {}".format(full_url)
    search_page = requests.get(full_url, verify=False)

    soup = BeautifulSoup(search_page.content, 'html.parser')
    ul = soup.find("ul", {"id": "thelist"})
    li_s = ul.find_all("li")

    if len(li_s) < 4:
        return "[-] No search result"

    target_li = li_s[3]
    target_a = target_li.find("a", class_="pic")

    target_url = "https://m.mobogenie.com" + target_a["href"]
    result_page = requests.get(target_url, verify=False)

    save_path = os.path.join(html_dir, package_name + "-" + md5)
    if os.path.isfile(save_path):
        #print "[~] Skipping {}, apk info already downloaded".format(package_name)
        return "[~] Skipped downloading " + str(package_name) + ", apk already downloaded"

    with open(save_path, 'a')as f:
        f.write(result_page.content)

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
