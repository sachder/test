import sqlite3
import os
from bs4 import BeautifulSoup
import pprint

db = sqlite3.connect("apkinfo.db")
html_dir = "temp_htmls/"

update_sql = " UPDATE MALWARES SET NAME = ?, RATING = ?, CATEGORY = ?, LAST_UPDATED = ?, VERSION = ? " \
                " WHERE PACKAGE = ? AND MD5 = ?"

def get_info(page_content, package_name, md5):
    soup = BeautifulSoup(page_content, 'html.parser')
    title = (soup.title.string).encode("utf-8").strip()

    if title.startswith("Apk Download"):
        return None

    # Name
    h1 = soup.find("h1", class_="name")
    name = h1.get_text()

    info_table = soup.find("table", class_="pdt-table")
    tds = info_table.findAll("td")

    info = ["version", "last_updated", "category", 0.0]  # version, last-updated, category, rating
    info_index = -1

    for td in tds:
        text = td.get_text()
        if info_index != -1:
            info[info_index] = text

        if text == "Last Updated":
            info_index = 1
        elif text == "App Version":
            info_index = 0
        elif text == "Category":
            info_index = 2
        elif text == "Content Rating":
            info_index = 3
        else:
            info_index = -1

    if info[0] == "version":
        version = "1.0"
    else:
        version = info[0]

    last_updated, category, rating = info[1:]

    return name, float(rating), category, last_updated, version, package_name, md5

cur = db.cursor()
if __name__ == '__main__':
    malwares = [f for f in os.listdir(html_dir) if os.path.isfile(os.path.join(html_dir, f))]
    print "[*] Found {} malwares".format(len(malwares))

    hit, miss = 0, 0
    for malware in malwares:
        with open(os.path.join(html_dir, malware)) as f:
            page_content = f.read()
        f.close()

        package_name, md5 = malware.split("-")

        print "[^] Parsing {} : {}".format(package_name, md5)

        apk_info = get_info(page_content, package_name, md5)

        if apk_info is not None:
            hit += 1
            db.execute(update_sql, apk_info)
            db.commit()
        else:
            miss += 1

    print "Tried to find info for {} malwares \n Hit: {}\n Miss: {}".format(len(malwares), hit, miss)
