from bs4 import BeautifulSoup
import requests
import pprint
import os
import sqlite3
from requests.packages.urllib3.exceptions import *

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Basic configuration and database connectivity
packages_dir = "packages/"
db = sqlite3.connect("apkinfo.db")
base_apkpure = "https://apkpure.com"
base_search  = "/search?q="


db.execute('''CREATE TABLE IF NOT EXISTS APP
        (PACKAGE	CHAR(200) PRIMARY KEY NOT NULL,
         NAME		CHAR(200) NOT NULL,
         RATING		REAL,
         CATEGORY	CHAR(100) NOT NULL,
         LAST_UPDATED	CHAR(20) NOT NULL,
         VERSION	REAL,
         DOWNLOAD_LINK	CHAR(2000));''');

insert_sql = ''' INSERT INTO app(PACKAGE, NAME, RATING, CATEGORY, LAST_UPDATED, VERSION, DOWNLOAD_LINK) 
                VALUES (?, ?, ?, ?, ?, ?, ?) '''
cat_exists_sql = ''' SELECT COUNT(*) FROM APP WHERE CATEGORY =? '''

print "[*] Database setup complete"
print "[*] Reading packages from {}".format(packages_dir)



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
    categories = [f for f in os.listdir(packages_dir) if os.path.isfile(os.path.join(packages_dir, f))]
    print "[*] Found {} categories".format(len(categories))

    for category in categories:
        print "[*] Current category: {}".format(category)
        cur = db.cursor()
        cur.execute(cat_exists_sql, (category,))
        exists = cur.fetchone()
        if exists[0] == 0:
            with open(packages_dir + category) as f:
                packages = f.read()

            packages = packages.split("\n")
            insert_cur = db.cursor()
            for package_name in packages:
                try:
                    package_info = get_app_info(package_name, category)
                    insert_cur.execute(insert_sql, package_info)
                except Exception as e:
                    print "\t[^] Error processing {}, probably not available".format(package_name)
            db.commit()
        else:
            print "\t[^] Category already processed, moving on ..."

