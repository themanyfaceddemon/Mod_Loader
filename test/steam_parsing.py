"""
import os

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)


def fetch_page(workshop_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
    response = session.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Failed to retrieve the page for ID: {workshop_id}")
        return None


def extract_author(soup):
    main_author_div = soup.find("div", class_="friendBlockContent")
    return (
        main_author_div.decode_contents().split("<br/>")[0].strip()
        if main_author_div
        else "Unknown Author"
    )


def extract_mod_name(soup):
    title_div = soup.find("div", class_="workshopItemTitle")
    return (
        title_div.get_text(strip=True).replace(" ", "_") if title_div else "UnknownMod"
    )


def parse_dependencies(soup, noisy=False):
    dependencies = []
    dependency_div = soup.find("div", class_="requiredItemsContainer")

    if not dependency_div:
        if noisy:
            print("No dependencies found on the page.")
        return dependencies

    for link in dependency_div.find_all("a", href=True):
        dependency_url = link["href"]

        try:
            dependency_id = dependency_url.split("id=")[1]
            dependency_name = link.get_text(strip=True)

            if dependency_id not in [dep["id"] for dep in dependencies]:
                dependencies.append(
                    {
                        "id": dependency_id,
                        "name": dependency_name,
                    }
                )
                if noisy:
                    print(f"Dependency found: {dependency_name} (ID: {dependency_id})")

        except IndexError:
            print(f"Failed to parse ID from URL: {dependency_url}")
            continue

    return dependencies


def fetch_dependencies(workshop_id, noisy=False):
    filename = f"test/auto_pars/{workshop_id}.xml"
    if os.path.exists(filename):
        print(f"Metadata file {filename} already exists. Skipping fetch.")
        return {}

    soup = fetch_page(workshop_id)
    if not soup:
        return {}

    main_author = extract_author(soup)
    mod_name = extract_mod_name(soup)
    dependencies = parse_dependencies(soup, noisy)

    return {
        "main_author": main_author,
        "mod_name": mod_name,
        "dependencies": dependencies,
    }


def generate_metadata_file(mod_id, data):
    filename = f"test/auto_pars/{mod_id}.xml"
    if os.path.exists(filename):
        print(f"Metadata file {filename} already exists. Skipping generation.")
        return

    metadata = ET.Element("metadata")
    comment = ET.Comment("This file was automatically generated.")
    metadata.append(comment)

    meta = ET.SubElement(metadata, "meta")
    ET.SubElement(meta, "author").text = data["main_author"]
    ET.SubElement(
        meta, "id"
    ).text = f"{data['main_author'].replace(' ', '')}.{data['mod_name']}"
    ET.SubElement(meta, "warning").text = "This dep was automatically generated!"

    if data["dependencies"]:
        dependencies = ET.SubElement(metadata, "dependencies")
        for dep in data["dependencies"]:
            ET.SubElement(
                dependencies,
                "requirement",
                name=dep["name"],
                steamID=dep["id"],
            )

    rough_string = ET.tostring(metadata, "utf-8")
    reparsed = minidom.parseString(rough_string)
    pretty_xml_as_string = "\n".join(
        [
            line
            for line in reparsed.toprettyxml(encoding="utf-8")
            .decode("utf-8")
            .splitlines()
            if line.strip()
        ]
    )
    with open(filename, "w", encoding="utf-8") as file:
        file.write(pretty_xml_as_string)

    print(f"Metadata file {filename} created.")


def get_mod_ids_from_page(url):
    response = session.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the page.")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    mod_ids = []

    for link in soup.find_all("a", href=True):
        if "/sharedfiles/filedetails/?id=" in link["href"]:
            try:
                mod_id = link["href"].split("id=")[1].split("&")[0]
                if mod_id not in mod_ids:
                    mod_ids.append(mod_id)
            except IndexError:
                continue

    return mod_ids


def parse_multiple_mods(workshop_ids, noisy=False):
    results = {}
    for workshop_id in workshop_ids:
        print(f"\nParsing mod ID: {workshop_id}")
        data = fetch_dependencies(workshop_id, noisy)
        if data:
            generate_metadata_file(workshop_id, data)
        results[workshop_id] = data
    return results


for i in range(1, 50):
    mod_ids = get_mod_ids_from_page(
        f"https://steamcommunity.com/workshop/browse/?appid=602960&browsesort=trend&section=readytouseitems&excludedtags%5B0%5D=Submarine&created_date_range_filter_start=0&created_date_range_filter_end=0&updated_date_range_filter_start=0&updated_date_range_filter_end=0&actualsort=trend&p={i}&days=-1"
    )
    parsed_mods = parse_multiple_mods(mod_ids, noisy=True)
"""
