from bs4 import BeautifulSoup
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
# Basic configuration and database connectivity
base_apkpure = "https://apkpure.com"
base_search  = "/search?q="
packages_dir = "packages/"
db = sqlite3.connect("apkinfo.db")
apks_dir = "apks/"
PACKAGE, NAME, RATING, CATEGORY, LAST_UPDATED, VERSION, DOWNLOAD_LINK = 0, 1, 2, 3, 4, 5, 6


update_sql = ''' UPDATE app SET DOWNLOAD_LINK = ? WHERE PACKAGE = ? '''

print "[*] Database setup complete"
print "[*] Reading applications from database"

applications = db.execute('SELECT * FROM APP').fetchall();

print "[*] Found {} applications".format(len(applications))

def get_app_info(package_name):
    full_url = base_apkpure + base_search + package_name
    print "[#] Getting information for package {}".format(package_name)
    print "\t[-] Requesting URL {}".format(full_url)
    search_page = requests.get(full_url, verify=False)
    soup = BeautifulSoup(search_page.content, 'html.parser')
    target_p = soup.find("p", class_="search-title")
    a_tag = target_p.find('a')

    info_url = base_apkpure + a_tag["href"]
    print "\t[-] Requesting URL {}".format(info_url)
    info_page = requests.get(info_url, verify=False)
    soup = BeautifulSoup(info_page.content, 'html.parser')

    # Download Link
    div_dl = soup.find("div", class_="ny-down")
    dll_stage1 = div_dl.find("a")["href"]
    dll_stage1 = base_apkpure + dll_stage1
    print "\t[-] Requesting URL {}".format(dll_stage1)
    download_page = requests.get(dll_stage1, verify=False)
    soup = BeautifulSoup(download_page.content, 'html.parser')
    dl_link = soup.find("a", {"id": "download_link"})
    time.sleep(10)
    return dl_link["href"]

def get_new_download_link(app):
    TIME_DELAY = 30
    print "[#] Checking if apk exists: {}".format(app[PACKAGE])
    save_path = str(apks_dir) + str(app[CATEGORY]) + "/"
    save_path = save_path + str(app[PACKAGE]) + ".apk"

    if os.path.isfile(save_path):
        print "[~] Skipping {}, apk already downloaded".format(app[PACKAGE])
        return "[~] Skipped downloading " + str(app[PACKAGE]) + ", apk already downloaded"

    try:
        dl_link = get_app_info(app[PACKAGE])
    except Exception as e:
        print "[-] Failed to get info, got exception {}".format(e)
        return "[-] Failed to get info, got exception {} " + str(e)
    update_cur = db.cursor()
    params = (dl_link, app[PACKAGE])
    update_cur.execute(update_sql, params)
    db.commit()
    update_cur.close()
    print "[+] Updated download link for {}".format(app[PACKAGE])
    return "[+] Updated download link for " + str(app[PACKAGE])


if __name__ == '__main__':
    pool = Pool(processes=10)
    results = pool.map(get_new_download_link, applications)
    pool.close()
    pool.join()

    print "\n\nFinal output:"
    print "------------------------------------------------------\n\n"
    pprint.pprint(results)
    exit()
