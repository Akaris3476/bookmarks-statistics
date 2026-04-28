import argparse
import datetime
import json
import os
import random
import time
from typing import Callable
from urllib.parse import urlparse
from selenium import webdriver
import selenium
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common import by
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import re

from bs4 import BeautifulSoup


class WebScrapper:

    def dispose(self):
        self.driver.quit()


    statistics: dict[str, int | dict ] = {}


    def __init__(self):

        self.statistics["total_count"] = 0
        self.statistics["total_words"] = 0
        self.statistics["Aborts"]: dict[str, int | list[str]] = { "Aborts Count": 0, "Aborts Urls": [], "Domain is unknown": 0, "Unknown urls": [] }
        self.statistics["fandoms"] = {}


        options = webdriver.ChromeOptions()

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)



    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    timeout = 15
    small_timeout = 7
    fail_retries = 6

    def make_request(self, url: str, wait_and_find: Callable[[WebDriver, int], WebElement]) -> BeautifulSoup | None:
        headers = self.headers
        fail_retries = self.fail_retries
        timeout = self.timeout
        driver = self.driver
        aborts_statistics: dict = self.statistics["Aborts"]


        driver.set_page_load_timeout(timeout)
        for attempt in range(fail_retries):
            try:
                print("initial waiting...")
                time.sleep(random.uniform(2, 5))

                driver.get(url)


                element = wait_and_find(driver, self.small_timeout)
                print("element found")
                # print(element.text)

                contents = driver.page_source

                htmlka = BeautifulSoup(contents, features="lxml")

                return htmlka

            except Exception as e:
                print("ERROR!!! Trying again...")
                print("error waiting...")
                time.sleep(random.uniform(5, 10))

                # print(f"ERROR!! {e}. Trying again...")


        aborts_statistics["Aborts Count"] += 1
        aborts_statistics["Aborts Urls"].append(url)
        print(f"ERROR!! Aborting")
        return None


    def ao3_scrap(self, url: str):
        statistics = self.statistics
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
            return


        words_count = htmlka.find("dd", class_="words").text.strip().replace(",", "")

        words_int = int(words_count)
        print(f"Words: {words_int:,}")



        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        # search for  dl class="stats"><dt class="words">Words:</dt><dd class="words">358,557</dd>

        # TODO: handle blue lock
        return

    def ffnet_scrap(self, url: str):
        statistics = self.statistics

        print(f"ffnet: {url}")

        def element_search(driver: WebDriver,timeout: int):
            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.CLASS_NAME, "xgray"))
            )
            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return

        ff_header = htmlka.find("span", class_="xgray").text

        # print(ff_header)

        words_section = re.search(r'Words:\s*(\d+(?:[,.]\d+)?)(?:[kK]\+)?', ff_header)

        print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k+" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        return

    def mffnet_scrap(self, url: str):
        statistics = self.statistics

        print(f"mffnet: {url}")

        def element_search(driver: WebDriver, timeout: int):
            element = WebDriverWait(driver, timeout).until(
                ec.presence_of_element_located((By.ID, "content"))
            )
            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return

        ff_header = htmlka.find("div", id="content").text

        # print(ff_header)

        words_section = re.search(r'Words:\s*(\d+(?:\.\d+)?)(?:[kK]\+)?', ff_header)

        print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k+" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        return

    def sb_scrap(self, url: str):
        # block-formSectionHeader
        statistics = self.statistics

        print(f"sb: {url}")

        def element_search(driver,timeout):
            try:
                close_btn = WebDriverWait(driver, timeout/2).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "fc-button-label"))
                )
                close_btn.click()
            except:
                pass


            try:
                element = WebDriverWait(driver, timeout).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "threadmark-control--index"))
                )
                element.click()
            except:
                pass


            element = WebDriverWait(driver, timeout).until(
                ec.visibility_of_element_located((By.CLASS_NAME, "block-formSectionHeader"))
            )

            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return

        ff_header = htmlka.find("div", class_="block-formSectionHeader").text

        # print(ff_header)
        pattern: str = r"(\d+)(.\d+)?(?:[kK]\swords)"
        words_section = re.search(pattern, ff_header)

        print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        return

    def sv_scrap(self, url: str):
        statistics = self.statistics

        print(f"sv: {url}")

        def element_search(driver,timeout):
            try:
                close_btn = WebDriverWait(driver, timeout/2).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "css-1jqk1n3"))
                )
                close_btn.click()
            except:
                pass


            try:
                element = WebDriverWait(driver, timeout).until(
                    ec.element_to_be_clickable((By.CLASS_NAME, "threadmark-control--index"))
                )
                element.click()
            except:
                pass


            element = WebDriverWait(driver, timeout).until(
                ec.visibility_of_element_located((By.CLASS_NAME, "block-formSectionHeader"))
            )

            return element

        htmlka = self.make_request(url, element_search)

        if htmlka is None:
            print(f"ERROR! htmlka is null")
            return

        ff_header = htmlka.find("div", class_="block-formSectionHeader").text

        # print(ff_header)
        pattern: str = r"(\d+)(.\d+)?(?:[kK]\swords)"
        words_section = re.search(pattern, ff_header)

        print(words_section.group(0))
        words_count = words_section.group(1).replace(",", "").replace(".", "")
        words_int = int(words_count)

        if "k" in words_section.group(0).lower():
            words_int *= 1000

        print(f"Words: {words_int:,}")

        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        return


    def web_scrapper_resolver(self, href: str):
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

        domain = urlparse(href).netloc

        if domain in ao3_domains:
            self.ao3_scrap(href)
            return

        if domain in sb_domains:
            self.sb_scrap(href)
            return

        if domain in sv_domains:
            self.sv_scrap(href)
            return

        if domain in ffnet_domains:
            if domain == "www.fanfiction.net":
                self.ffnet_scrap(href)
                return
            else:
                self.mffnet_scrap(href)
                return



        self.statistics["Aborts"]["Domain is unknown"] += 1
        self.statistics["Aborts"]["Unknown urls"].append(href)


    def scrap(self, url: str):
        self.web_scrapper_resolver(url)


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


def folder_case(stat: dict, element, scrapper: WebScrapper):

    # dt - titles


    for child in element.find_all("dt", recursive=False):

        title = child.find("h3", recursive=False)
        if title:
            title = title.text
            stat[title] = {}
            print(title)
            folder = child.find_next_sibling("dl", recursive=False)
            folder_case(stat[title], folder, scrapper)



        stat["fics"] = []

        # TODO add_Date class in vscode
        stat["add_date"] = []

        links = child.find_all("a")

        if links:

            for link in links:
                link = link.get("href")
                # scrapper.web_scrapper_resolver(link)
                print()
                stat["fics"].append(link.strip())
                # print(link)


def bookmark_calculate(html_filepath: str) -> WebScrapper:
    bookmarks = read_and_parse_html(html_filepath)

    if not bookmarks:
        exit(1)

    # folder where fanfics stored
    fanfics_dt = bookmarks.find("h3", string="Прочитано")

    if fanfics_dt is None:
        print('No "Прочитано" folder found')
        exit(1)
    print(fanfics_dt.text)
    print()

    fanfics = fanfics_dt.find_next('dl')


    web_scrapper = WebScrapper()

    try:
        # for dt in fanfics.find_all('dt', recursive=False, limit=None):
        #
        #     folder_case(dt)
        #     for link in dt.find_all('a'):
        #         # print(link.text.strip())
        #         href = link.get('href')
        #         web_scrapper.scrap(href)
        #         print()
        # for fan in fanfics.children:
        #     # def folder_case():
        #     #     web_scrapper.statistics[] = { }
        #
        #
        #
        #     print(fan.text)
        folder_case(web_scrapper.statistics["fandoms"], fanfics, web_scrapper)

    finally:
        web_scrapper.dispose()

    return web_scrapper





def main():

    arg_parser = argparse.ArgumentParser(description='Calculates amount of words of fanfics in bookmarks')
    arg_parser.add_argument('input', type = str, nargs="+", default=None, help = 'Path to html file')

    args = arg_parser.parse_args()

    html_filepath: str = args.input[0]

    if html_filepath is None:
        print('No arguments provided')
        exit(1)

    web_scrapper = bookmark_calculate(html_filepath)

    # web_scrapper = WebScrapper()
    # web_scrapper.scrap("")

    statistics = web_scrapper.statistics

    bookmark_date = re.search(r"bookmarks_(\d)+_(\d+)_(\d+)", html_filepath)
    day = bookmark_date.group(2)
    month = bookmark_date.group(1)
    year = bookmark_date.group(3)
    bookmark_date = datetime.date(int(year)+2000, int(month), int(day))

    info = {"datetime": f"{datetime.datetime.now().isoformat()}",
            "bookmark_date": f"{bookmark_date.isoformat()}",
            "scrapped_info": statistics }
    print(json.dumps(info, indent=4, sort_keys=True, ensure_ascii=False))
    print(f"{statistics['total_words']:,}")






if __name__ == '__main__':
    main()