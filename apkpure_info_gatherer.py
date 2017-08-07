from bs4 import BeautifulSoup
import requests
import pprint
import os
import sqlite3
from requests.packages.urllib3.exceptions import *

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Basic configuration and database connectivity
apks_dir = "/home/avs/Desktop/datasets/apks/"
db = sqlite3.connect("apkinfo.db")
base_apkpure = "https://apkpure.com"
base_search  = "/search?q="

all_apps = []

cur = db.cursor()
cur.execute("SELECT PACKAGE FROM APP")
for row in cur.fetchall():
    all_apps.append(row[0])

cur.close()

insert_sql = ''' INSERT INTO app(PACKAGE, NAME, RATING, CATEGORY, LAST_UPDATED, VERSION, DOWNLOAD_LINK) 
                VALUES (?, ?, ?, ?, ?, ?, ?) '''
cat_exists_sql = ''' SELECT COUNT(*) FROM APP WHERE CATEGORY =? '''

print "[*] Database setup complete"
print "[*] Reading packages from {}".format(apks_dir)



def get_app_info(package_name, category):
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
    app_info = {}

    # Name
    div_title = soup.find("div", class_="title-like")
    h1_title  = div_title.find("h1")
    app_info["name"] = h1_title.get_text()

    # Package Name and Category
    app_info["package"] = package_name
    app_info["category"] = category

    # Version
    version_ul = soup.find("ul", class_="version-ul")
    p_tags     = version_ul.findAll("p")
    app_info["version"] = p_tags[3].get_text()
    app_info["last_updated"] = p_tags[5].get_text()

    # Rating
    span_rating = soup.find("span", class_="average")
    app_info["rating"] = span_rating.get_text()

    # Download Link
    div_dl = soup.find("div", class_="ny-down")
    dll_stage1 = div_dl.find("a")["href"]
    dll_stage1 = base_apkpure + dll_stage1
    print "\t[-] Requesting URL {}".format(dll_stage1)
    download_page = requests.get(dll_stage1, verify=False)
    soup = BeautifulSoup(download_page.content, 'html.parser')
    dl_link = soup.find("a", {"id": "download_link"})

    app_info["download_link"] = dl_link["href"]

    return (app_info["package"], app_info["name"], app_info["rating"], app_info["category"],
            app_info["last_updated"], app_info["version"], app_info["download_link"])


if __name__ == '__main__':
    categories = [f for f in os.listdir(apks_dir) if os.path.isdir(os.path.join(apks_dir, f))]
    print "[*] Found {} categories".format(len(categories))
    count = 0
    cur = db.cursor()
    cats = 0
    for category in categories:
        print ""
        print "[*] Current category: {}".format(category)
        print ""
        cats += 1

        cat_path = os.path.join(apks_dir, category)
        apks = [f for f in os.listdir(cat_path) if os.path.isfile(os.path.join(cat_path, f))]
        for apk in apks:
            count += 1
            file_name = apk.split(".")
            package_name = ".".join(file_name[:len(file_name) - 1])

            if package_name in all_apps:
                print "[-] Already Processed {}".format(package_name)
                continue
            try:
                package_info = get_app_info(package_name, category)
                cur.execute(insert_sql, package_info)

                print "[+] Processed {}".format(package_name)
            except Exception as e:
                print "Got exception: {}".format(e)

        db.commit()

    print "Processed {} apks in {} categories".format(count, cats)
    print "Versus all apps: {}".format(len(all_apps))
