import argparse
import os
import random
import time
from urllib.parse import urlparse
import requests

from bs4 import BeautifulSoup


def ao3_scrap(url: str):
    time.sleep(random.uniform(2, 5))

    print(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    timeout = 10
    contents = requests.get(url, timeout=timeout, headers=headers,)

    for _ in range(2):
        if contents.status_code != 200:
            print(f"ERROR! Status_code: {contents.status_code}. Trying again...")
            contents = requests.get(url, timeout=timeout, headers=headers, )

    if contents.status_code != 200:
        print(f"ERROR! Status_code: {contents.status_code}. Aborting...")
        return

    if contents.status_code == 200:
        print(contents)

        htmlka = BeautifulSoup(contents.text, features="lxml")
        words = htmlka.find("dd", class_="words").text.strip().replace(",", "")

        words_int = int(words)
        print(words_int)



        statistics["total_count"] += 1
        statistics["total_words"] += words_int

        # search for  dl class="stats"><dt class="words">Words:</dt><dd class="words">358,557</dd>

        # TODO: handle blue lock
        return

    return

def ffnet_scrap(url: str) -> int:
    return 4

def sb_scrap(url: str) -> int:
    return 3

def read_and_parse_html(html_filepath: str) -> BeautifulSoup | None:
    print(f'Reading {html_filepath}')

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


# def folder_case():
    # iterate next

# def link_case(url):
    # web parser logic


statistics: dict[str, int] = {}

def web_scrapper_resolver(href: str):
    ao3_domains = { "archiveofourown.com", "archiveofourown.net", "archiveofourown.gay",
                    "ao3.org",
                    "archiveofourown.org",
                    "archive.transformativeworks.org",
                    "insecure.archiveofourown.org", "secure.archiveofourown.org",
                    "download.archiveofourown.org",
                    "www.archiveofourown.com","www.archiveofourown.net","www.archiveofourown.org", "www.ao3.org" }

    ffnet_domains = { "www.fanfiction.net",
                      "m.fanfiction.net" }

    sb_domains = { "forums.spacebattles.com" }

    domain = urlparse(href).netloc


    if domain in ao3_domains:
        ao3_scrap(href)

    if domain in ffnet_domains:
        ffnet_scrap(href)

    if domain in sb_domains:
        sb_scrap(href)



def bookmark_calculate(html_filepath: str):
    bookmarks = read_and_parse_html(html_filepath)

    if not bookmarks:
        exit(1)

    fanfics_dt = bookmarks.find("h3", string="Прочитано")

    if fanfics_dt is None:
        print('No "Прочитано" folder found')
        exit(1)
    print(fanfics_dt.text)

    fanfics = fanfics_dt.find_next('dl')

    statistics["total_count"] = 0
    statistics["total_words"] = 0

    for dt in fanfics.find_all('dt', recursive=False, limit=None):

        for link in dt.find_all('a'):
            # print(link.text.strip())
            href = link.get('href')
            web_scrapper_resolver(href)

        # for






def main():

    arg_parser = argparse.ArgumentParser(description='Calculates amount of words of fanfics')
    arg_parser.add_argument('input', type = str, nargs="+", default=None, help = 'Path to html file')

    args = arg_parser.parse_args()

    html_filepath: str = args.input[0]

    if html_filepath is None:
        print('No arguments provided')
        exit(1)

    bookmark_calculate(html_filepath)

    for stat in statistics:
        print(f'{stat}: {statistics[stat]}')


if __name__ == '__main__':
    main()