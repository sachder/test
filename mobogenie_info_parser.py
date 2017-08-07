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

    if package_name not in page_content:
        return None

    # Name
    p = soup.find("p", class_="app-name")
    name = p.get_text()

    b = soup.find("b", class_="star-num")
    rating = float(b.get_text())

    uls = soup.find("ul", class_="information-box")
    li_s = uls.find_all("li")

    version, last_updated, category = "1.0", "last-updated", "category"

    for li in li_s:
        h3 = li.find("h3").get_text()
        if h3 == "Version":
            version = li.find("p").get_text()
        elif h3 == "Updated":
            last_updated = li.find("p").get_text().split(" ")[0]
        elif h3 == "Category":
            category = li.find("a").get_text()

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
            pprint.pprint(apk_info)
            hit += 1
            db.execute(update_sql, apk_info)
            db.commit()
        else:
            miss += 1

    print "Tried to find info for {} malwares \n Hit: {}\n Miss: {}".format(len(malwares), hit, miss)
