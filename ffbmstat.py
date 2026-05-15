import argparse
import datetime
import json
import os
import random
import time
from json import JSONDecodeError
from typing import Callable
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import re

from bs4 import BeautifulSoup, Tag


class Cache:
    def __init__(self, filename: str):
        self.filename = filename
        self.cached_stat = self._load_cache(self.filename)

    def _load_cache(self, filename: str) -> dict:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding="utf-8") as f:
                    print(f"Reading from cache: {filename}")
                    return json.load(f)

            except JSONDecodeError:
                print("JSONDecodeError in cache")
                return {"datetime": f"{datetime.datetime.now().isoformat()}",
                        "words_stats": {}}

        else:
            with open(filename, 'w', encoding="utf-8") as f:
                print(f"Creating new cache file {self.filename}")
                return {"datetime": f"{datetime.datetime.now().isoformat()}",
                        "words_stats": {}}

    def get(self, key: str) -> int | None:
        if key in self.cached_stat["words_stats"]:
            return self.cached_stat["words_stats"][key]
        else:
            return None

    def set(self, key: str, value: int) -> None:
        self.cached_stat["words_stats"][key] = value

    def write(self):
        json.dump(self.cached_stat, open(self.filename, 'w', encoding="utf-8"), ensure_ascii=False, indent=4)
        print("Cache written")


class WebScraper:

    # def dispose(self):
    #     self.driver.quit()

    statistics: dict[str, int | dict ] = {}

    def __init__(self):

        self.cache = None
        self.statistics["Aborts"]: dict[str, int | list[str]] = { "Aborts Count": 0,
                                                                  "Aborts Urls": [],
                                                                  "Domain is unknown": 0,
                                                                  "Unknown urls": [] }
        self.statistics["fandoms"] = {}


        options = webdriver.ChromeOptions()

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        # options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)


    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    #     "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    # }
    timeout = 15
    small_timeout = 7
    fail_retries = 3

    def make_request(self, url: str, wait_and_find: Callable[[WebDriver, int], WebElement]) -> BeautifulSoup | None:
        # headers = self.headers
        fail_retries = self.fail_retries
        timeout = self.timeout
        driver = self.driver
        aborts_statistics: dict = self.statistics["Aborts"]


        driver.set_page_load_timeout(timeout)

        for attempt in range(fail_retries):
            try:
                print("initial waiting...")
                time.sleep(random.uniform(3, 6))

                driver.get(url)

                element = wait_and_find(driver, self.small_timeout)
                print("element found")
                # print(element.text)

                contents = driver.page_source

                htmlka = BeautifulSoup(contents, features="lxml")

                return htmlka

            except Exception as e:
                print("ERROR!!! Waiting before trying again...")
                print()
                time.sleep(random.uniform(7, 11))


        aborts_statistics["Aborts Count"] += 1
        aborts_statistics["Aborts Urls"].append(url)
        print(f"ERROR!! Aborting")
        return None


    def ao3_scrap(self, url: str) -> int:
        print(f"ao3: {url}")

        def element_search(driver: WebDriver,timeout: int):
            print("waiting for element...")
            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "words"))
            )
            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1


        words_count = htmlka.find("dd", class_="words").text.strip().replace(",", "")

        words_int = int(words_count)
        print(f"Words: {words_int:,}")

        # search for  dl class="stats"><dt class="words">Words:</dt><dd class="words">358,557</dd>

        # TODO: handle locked out titles (i.e. blue lock) (solved with logging in in browser before scraping)
        return words_int

    def ffnet_scrap(self, url: str) -> int:
        print(f"ffnet: {url}")

        def element_search(driver: WebDriver,timeout: int):
            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "xgray"))
            )
            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1

        ff_header = htmlka.find("span", class_="xgray").text

        # print(ff_header)

        words_section = re.search(r'Words:\s*(\d+(?:[,.]\d+)?)(?:[kK]\+)?', ff_header)

        # print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k+" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        return words_int

    def mffnet_scrap(self, url: str) -> int:
        print(f"mffnet: {url}")

        def element_search(driver: WebDriver, timeout: int):
            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.ID, "content"))
            )
            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1

        ff_header = htmlka.find("div", id="content").text

        # print(ff_header)

        words_section = re.search(r'Words:\s*(\d+(?:\.\d+)?)(?:[kK]\+)?', ff_header)

        # print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k+" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        return words_int

    def sb_scrap(self, url: str) -> int:
        # block-formSectionHeader

        print(f"sb: {url}")

        def element_search(driver,timeout):
            # try:
            #     close_btn = WebDriverWait(driver, timeout/2).until(
            #         ec.element_to_be_clickable((By.CLASS_NAME, "fc-button-label"))
            #     )
            #     close_btn.click()
            # except:
            #     pass

            try:
                element = WebDriverWait(driver, timeout).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "threadmark-control--index"))
                )
                element.click()
            except:
                pass


            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "block-formSectionHeader"))
            )

            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1

        ff_header = htmlka.find("div", class_="block-formSectionHeader").text

        # print(ff_header)
        pattern: str = r"(\d+)(.\d+)?(?:[kK]\swords)"
        words_section = re.search(pattern, ff_header)

        # print(words_section.group(0))
        if words_section is None:
            print("WARNING! Pattern not found. Returning 0")
            return 0
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        return words_int

    def sv_scrap(self, url: str) -> int:
        print(f"sv: {url}")

        def element_search(driver,timeout):
            # try:
            #     close_btn = WebDriverWait(driver, timeout/2).until(
            #         ec.element_to_be_clickable((By.CLASS_NAME, "css-1jqk1n3"))
            #     )
            #     close_btn.click()
            # except:
            #     pass

            try:
                element = WebDriverWait(driver, timeout).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "threadmark-control--index"))
                )
                element.click()
            except:
                pass

            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "block-formSectionHeader"))
            )

            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1

        ff_header = htmlka.find("div", class_="block-formSectionHeader").text

        # print(ff_header)
        pattern: str = r"(\d+)(.\d+)?(?:[kK]\swords)"
        words_section = re.search(pattern, ff_header)

        # print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        return words_int

    def ficbook_scrap(self, url: str) -> int:
        print(f"fb: {url}")

        def element_search(driver,timeout):
            # try:
            #     close_btn = WebDriverWait(driver, timeout/2).until(
            #         ec.element_to_be_clickable((By.CLASS_NAME, "ds-btn-primary"))
            #     )
            #     close_btn.click()
            # except:
            #     pass

            element = WebDriverWait(driver, timeout).until(
                ec.visibility_of_element_located((By.CLASS_NAME, "description"))
            )

            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return 1

        ff_header = htmlka.find("div", class_="description").text
        # print(ff_header)

        pattern: str = r",\s(\d+(?:\s\d+)?)\sслов(?:[ао])?,"
        words_section = re.search(pattern, ff_header)

        # print(words_section.group(0))
        words_count = words_section.group(1).replace("\xa0", "")
        words_int = int(words_count)

        print(f"Words: {words_int:,}")

        return words_int

    def check_cache(self, href: str) -> int | None:
        if self.cache:
            return self.cache.get(href)
        return None

    def set_cache(self, cache: Cache) -> None:
        self.cache = cache

    def web_scraper_resolver(self, href: str) -> int:
        cached_value = self.check_cache(href)
        if cached_value:
            print(f"Cache hit: {href}")
            print(f"Words: {cached_value:,}\n")
            return cached_value

        ao3_domains = {"archiveofourown.com", "archiveofourown.net", "archiveofourown.gay",
                       "ao3.org",
                       "archiveofourown.org",
                       "archive.transformativeworks.org",
                       "insecure.archiveofourown.org", "secure.archiveofourown.org",
                       "download.archiveofourown.org",
                       "www.archiveofourown.com", "www.archiveofourown.net", "www.archiveofourown.org", "www.ao3.org"}

        ffnet_domains = {"www.fanfiction.net",
                         "m.fanfiction.net"}

        sb_domains = {"forums.spacebattles.com"}

        sv_domains = {"forums.sufficientvelocity.com"}

        ficbook_domains = {"ficbook.net"}

        domain = urlparse(href).netloc

        print()

        words_count = 0
        if domain in ao3_domains:
            words_count = self.ao3_scrap(href)

        if domain in sb_domains:
            words_count = self.sb_scrap(href)


        if domain in sv_domains:
            words_count = self.sv_scrap(href)


        if domain in ffnet_domains:
            if domain == "www.fanfiction.net":
                words_count = self.ffnet_scrap(href)
            else:
                words_count = self.mffnet_scrap(href)


        if domain in ficbook_domains:
            words_count = self.ficbook_scrap(href)


        if words_count != 0:
            self.cache.set(href, words_count)
            return words_count

        # DEBUG
        # if domain in ao3_domains:
        #     return 2
        #
        # if domain in sb_domains:
        #     return 7
        #
        # if domain in sv_domains:
        #     return 3
        #
        # if domain in ficbook_domains:
        #     return 3
        #
        # if domain in ffnet_domains:
        #     if domain == "www.fanfiction.net":
        #         return 5
        #     else:
        #         return 4

        self.statistics["Aborts"]["Domain is unknown"] += 1
        self.statistics["Aborts"]["Unknown urls"].append(href)
        return 0


    def scrap(self, url: str) -> int:
        return self.web_scraper_resolver(url)


def read_and_parse_html(html_filepath: str) -> BeautifulSoup | None:
    print(f'Reading {html_filepath}\n')

    if not os.path.exists(html_filepath):
        filename = html_filepath.split('/')[-1]
        print(f'{filename} not found. Invalid argument')
        return None

    if not html_filepath.endswith('.html'):
        filename = html_filepath.split('/')[-1]
        print(f'{filename} is not .epub. Invalid argument')
        return None

    with open(html_filepath, 'r', encoding="utf-8") as f:
        content = f.read()
        soupchik = BeautifulSoup(content, features="lxml")
        return soupchik


def traverse_html_tree(stat: dict, element: Tag, scraper: WebScraper) -> dict:

    # -------------Initialize-bookmarks-stat-----------

    stat["fics"] = []
    if "stats" not in stat:
        stat["stats"] = {"words": {"Годно": 0, "Мелочь": 0, "Хрень": 0},
                         "count": {"Годно": 0, "Мелочь": 0, "Хрень": 0},
                         "add_dates": []}


    #----------------Start-iterating--------------------

    # looks for every child of a tag. dt contains either a folder name or <a> tag with bookmark link
    for child in element.find_all("dt", recursive=False):

        #-------------Check-bookmarks-links---------------

        # find links inside tag
        links = child.find_all("a")

        if links:
            for link in links:
                href = link.get("href").strip()
                fic = {"link": href, "words": 0, "add_date": None}

                words = scraper.scrap(href)
                fic["words"] = words

                dl_parent = link.find_parent("dl")
                if dl_parent:
                    folder_name = dl_parent.find_previous_sibling("dt").find("h3", recursive=False)
                    if folder_name:
                        folder_name = folder_name.text.lower()
                        if folder_name == "мелочь":
                            stat["stats"]["words"]["Мелочь"] += words
                            stat["stats"]["count"]["Мелочь"] += 1
                        elif folder_name == "хрень":
                            stat["stats"]["words"]["Хрень"] += words
                            stat["stats"]["count"]["Хрень"] += 1
                        else:
                            stat["stats"]["words"]["Годно"] += words
                            stat["stats"]["count"]["Годно"] += 1
                    else:
                        stat["stats"]["words"]["Годно"] += words
                        stat["stats"]["count"]["Годно"] += 1

                add_date = link.get("add_date")
                stat["stats"]["add_dates"].append(add_date)
                fic["add_date"] = add_date
                stat["fics"].append(fic)

        #--------------Folder-check----------------------


        # looks for folder name
        title = child.find("h3", recursive=False)
        # if folder name exists, there is a folder. recursively check it
        if title:
            title = title.text
            stat[title] = {}
            # print(title)

            # folder stored in dl tag nearby
            folder = child.find_next_sibling("dl", recursive=False)
            if folder:
                stats = traverse_html_tree(stat[title], folder, scraper)
                # print(stats)
                stat["stats"]["words"]["Годно"] += stats["words"]["Годно"]
                stat["stats"]["count"]["Годно"] += stats["count"]["Годно"]

                stat["stats"]["words"]["Мелочь"] += stats["words"]["Мелочь"]
                stat["stats"]["count"]["Мелочь"] += stats["count"]["Мелочь"]

                stat["stats"]["words"]["Хрень"] += stats["words"]["Хрень"]
                stat["stats"]["count"]["Хрень"] += stats["count"]["Хрень"]


    return stat["stats"]


def bookmark_calculate(html_filepath: str, cache_filepath: str | None) -> WebScraper:
    bookmarks = read_and_parse_html(html_filepath)

    if not bookmarks:
        exit(1)

    # folder where fics stored
    fics_dt = bookmarks.find("h3", string="Прочитано")

    if fics_dt is None:
        print('No "Прочитано" folder found')
        exit(1)
    print(f"Fics folder: '{fics_dt.text}'")
    print()

    fics = fics_dt.find_next('dl')
    if fics is None:
        raise Exception("No fics found")


    web_scraper = WebScraper()

    # TODO: cache path validation
    if cache_filepath is not None:
        cache_filename = cache_filepath.split('/')[-1]
    else:
        cache_filename = f"cache_bookmarks_{datetime.date.today()}.json"

    web_scraper.set_cache(Cache(cache_filename))

    input("Giving you time for preparation. Press any key to continue...")


    try:
        stats = traverse_html_tree(web_scraper.statistics["fandoms"], fics, web_scraper)
        print(stats)

        stat = web_scraper.statistics
        stat["total_stats"] = {"total_words": 0, "total_count": 0}

        stat["total_stats"]["total_words"] += stats["words"]["Годно"]
        stat["total_stats"]["total_count"] += stats["count"]["Годно"]

        stat["total_stats"]["total_words"] += stats["words"]["Мелочь"]
        stat["total_stats"]["total_count"] += stats["count"]["Мелочь"]

        stat["total_stats"]["total_words"] += stats["words"]["Хрень"]
        stat["total_stats"]["total_count"] += stats["count"]["Хрень"]

    finally:
        web_scraper.cache.write()
        # web_scraper.dispose()
        print()

    return web_scraper


def append_datetime(html_filepath: str, stat, cache_filename: str) -> dict:
    bookmark_date = re.search(r"bookmarks_(\d)+_(\d+)_(\d+)", html_filepath)
    if bookmark_date is None:
        print('No bookmark_date found')
        bookmark_date = datetime.date.fromisoformat("1970-01-01")
    else:
        day = bookmark_date.group(2)
        month = bookmark_date.group(1)
        year = bookmark_date.group(3)
        bookmark_date = datetime.date(int(year)+2000, int(month), int(day))

    stat = {"datetime": f"{datetime.datetime.now().isoformat()}",
            "bookmark_date": f"{bookmark_date.isoformat()}",
            "used_cache": cache_filename,
            "scraped_info": stat }

    return stat

def write_json(html_filepath: str, stat: dict):

    filename = os.path.basename(html_filepath).removesuffix(".html")
    filename = f"stat_{filename}.json"
    with open(filename, 'w', encoding="utf-8") as f:
        json.dump(stat, f, ensure_ascii=False, indent=4)

def main():

    arg_parser = argparse.ArgumentParser(description='Calculates amount of words of fanfics in bookmarks')
    arg_parser.add_argument('bookmarks_file', type = str, default=None, help = 'Path to html file')
    arg_parser.add_argument('cache_file', type = str, nargs="?", default=None, help = 'Path to cache file. '
                                                                                      'Notice, it takes only filename. '
                                                                                      'Cache will be written only in directory of this file.')
    # cache arg here only to take desirable file name to read in case of multiple cache files
    # all cache needed to be in the same directory as this file

    args = arg_parser.parse_args()

    html_filepath: str = args.bookmarks_file
    cache_filepath: str = args.cache_file

    if html_filepath is None:
        print('No arguments provided')
        exit(1)

    web_scraper = bookmark_calculate(html_filepath, cache_filepath)

    # debug. scraps only one link
    # web_scraper = WebScraper()
    # web_scraper.scrap("")

    statistics = web_scraper.statistics

    statistics = append_datetime(html_filepath, statistics, web_scraper.cache.filename)

    # print(json.dumps(statistics, indent=4, sort_keys=False, ensure_ascii=False))

    write_json(html_filepath, statistics)



if __name__ == '__main__':
    main()