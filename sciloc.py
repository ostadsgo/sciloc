import os
import re
from collections import Counter

import matplotlib.pyplot as plt
import requests
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

import predefined

FILENAME = "scientists.html"
BASE_URL = "https://fa.wikipedia.com"
PAGES_PATH = "scientists"
KEYWORDS = ["زادهٔ", "زاده", "محل زندگی"]


def is_exist_file(filename: str):
    return os.path.exists(filename)


def savefile(filename: str, text: str) -> bool:
    with open(filename, "w", encoding="utf-8") as file:
        try:
            file.write(text)
        except Exception as e:
            print(e)
            return True
    return False


def readfile(filename: str) -> str:
    print(filename)
    content = ""
    try:
        with open(filename, encoding="utf-8") as file:
            content = file.read()
            print(len(content))
    except Exception as e:
        print(e)
    return content


def read_webpage(page_url: str) -> str:
    """Read page_url and return html document as text."""
    html_doc = ""
    try:
        r = requests.get(page_url)
        if r.status_code == 200:
            html_doc = r.text
    except RequestException:
        print("Error: Request exception error occured!")
    return html_doc


def make_soup(html_doc: str):
    return BeautifulSoup(html_doc, "html.parser")


def scientist_table(soup: BeautifulSoup):
    """Extract table of scientists."""
    table = soup.table
    if table is not None:
        return table
    raise ValueError("There is no table to pares.")


def get_infobox(soup):
    return soup.find("table", class_="infobox")


def extract_scientists(table):
    """Extract name and link to each scientis' page."""
    # each scientis info saved as dict with name and link to their page
    scientists = []
    table_rows = table.find_all("tr")
    for row in table_rows:
        scientist = row.find_all("td")[1]
        name = scientist.text.strip()
        link = BASE_URL + scientist.a["href"]
        scientist = {"name": name, "link": link}
        scientists.append(scientist)
    return scientists


def save_scientists(scientists: list[dict[str, str]]):
    for index, scientist in enumerate(scientists, 1):
        _, link = scientist.values()
        filename = f"{PAGES_PATH}/{index}.html"
        if not is_exist_file(filename):
            html_doc = read_webpage(link)
            soup = make_soup(html_doc)
            if get_infobox(soup):
                savefile(filename, html_doc)


def is_city(places):
    for city in predefined.cities:
        if city in places:
            return city


def get_birthpalce(infobox):
    birthplace = infobox.find("span", class_="birthpalce").text.split()[0]
    return birthplace


def clear_raw_data(raw_data):
    raw_data = raw_data.replace("،", " ")
    raw_data = raw_data.replace("هجری", "")
    raw_data = raw_data.replace("خورشیدی", "")
    raw_data = raw_data.replace("مـ.", "")
    raw_data = raw_data.replace("هـ.", "")
    raw_data = raw_data.replace("میلادی", "")
    raw_data = raw_data.replace("قمری", "")
    raw_data = raw_data.replace("(", "")
    raw_data = raw_data.replace(")", "")
    raw_data = raw_data.replace("'", "")
    raw_data = raw_data.replace("[", "")
    raw_data = raw_data.replace("]", "")
    raw_data = raw_data.replace("ه.ق", "")
    raw_data = re.sub(r"\d+", "", raw_data)
    return raw_data


def extract_scientist_city(soup):
    infobox = get_infobox(soup)
    for keyword in KEYWORDS:
        find_result = infobox.find("th", string=keyword)
        if find_result:
            raw_data = find_result.next_sibling.text.strip()
            raw_data = clear_raw_data(raw_data)
            places = [place.strip() for place in raw_data.split()]
            city = is_city(places)
            if city:
                return city
    return "نامشخص"


def extract_scientist_name(soup):
    found_name = soup.find("span", class_="mw-page-title-main")
    if found_name:
        return found_name.text.strip()
    return ""


# This tooks more than usual - I don't like it.
def sort_by_article_length(data):
    return sorted(data, key=lambda record: record.get("article_len"), reverse=True)


# May: Change name of this function.
def get_data():
    """save data as a csv file."""
    data = []
    for html_file in os.listdir(PAGES_PATH):
        html_doc = readfile(f"{PAGES_PATH}/{html_file}")
        soup = make_soup(html_doc)
        article_len = int(len(soup.get_text()))
        if article_len > 20_000:
            print(html_file)
            name = extract_scientist_name(soup)
            city = extract_scientist_city(soup)
            record = {"article_len": article_len, "name": name, "city": city}
            data.append(record)
    print("Sroting ..")
    sorted_data = sort_by_article_length(data)
    return sorted_data


def save_data(data):
    lines = ""
    for record in data:
        name = record.get("name")
        city = record.get("city")
        line = f"{name},{city}\n"
        lines += line
    savefile("data.txt", lines)

def count_city_catory(extracted_cities):
    city_category = dict.fromkeys(predefined.city_category.keys(), 0)
    for category, cities in predefined.city_category.items():
        for extracted_city in extracted_cities:
            if extracted_city in cities:
                city_category[category] += 1
    
    return city_category




def draw_chart(data):
    rows = data.split("\n")
    rows = [row.strip() for row in rows if row]
    names = []
    cities = []
    for row in rows:
        name, city = row.split(",")
        names.append(name)
        cities.append(city)

    city_category_count = count_city_catory(cities)
    labels = city_category_count.keys()
    rtl_labels = [get_display(reshape(label)) for label in labels]
    sizes = city_category_count.values()

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=rtl_labels, autopct="%1.1f%%")
    plt.show()


def parse(html_doc: str):
    """Parse html page."""
    # if scientists html page is not saved in computer
    if not is_exist_file(PAGES_PATH):
        soup = make_soup(html_doc)
        table = scientist_table(soup)
        scientists = extract_scientists(table)
        save_scientists(scientists)
    # if pages alredy saved (no need to send request and get data agin)
    else:
        if is_exist_file("data.txt"):
            data = readfile("data.txt")
            draw_chart(data)
        else:
            data = get_data()
            save_data(data)


def main():
    if is_exist_file(FILENAME):
        html_doc = readfile(FILENAME)
    else:
        url = "https://fa.wikipedia.org/wiki/%D9%81%D9%87%D8%B1%D8%B3%D8%AA_%D8%AF%D8%A7%D9%86%D8%B4%D9%85%D9%86%D8%AF%D8%A7%D9%86_%D8%A7%DB%8C%D8%B1%D8%A7%D9%86%DB%8C_%D9%BE%DB%8C%D8%B4_%D8%A7%D8%B2_%D8%AF%D9%88%D8%B1%D8%A7%D9%86_%D9%85%D8%B9%D8%A7%D8%B5%D8%B1"
        html_doc = read_webpage(url)
        savefile(FILENAME, html_doc)
        html_doc = readfile(FILENAME)

    parse(html_doc)


if __name__ == "__main__":
    main()
