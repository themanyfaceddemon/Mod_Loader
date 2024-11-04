import requests
from bs4 import BeautifulSoup


def fetch_page(workshop_id):
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print("Failed to retrieve the page.")
        return None


def extract_author(soup):
    main_author_div = soup.find("div", class_="friendBlockContent")
    return (
        main_author_div.decode_contents().split("<br/>")[0].strip()
        if main_author_div
        else "Unknown Author"
    )


def parse_dependencies(soup, noisy=False):
    dependencies = []
    dependency_div = soup.find("div", class_="requiredItemsContainer")

    if not dependency_div:
        print("No dependencies found on the page.")
        return dependencies

    for link in dependency_div.find_all("a", href=True):
        dependency_url = link["href"]

        try:
            dependency_id = dependency_url.split("id=")[1]
            dependency_name = link.get_text(strip=True)

            author_div = link.find_next("div", class_="friendBlockContent")
            dependency_author = (
                author_div.decode_contents().split("<br/>")[0].strip()
                if author_div
                else "Unknown Author"
            )

            if dependency_id not in [dep["id"] for dep in dependencies]:
                dependencies.append(
                    {
                        "id": dependency_id,
                        "name": dependency_name,
                        "author": dependency_author,
                    }
                )
                if noisy:
                    print(
                        f"Dependency found: {dependency_name} (ID: {dependency_id}) by {dependency_author}"
                    )

        except IndexError:
            print(f"Failed to parse ID from URL: {dependency_url}")
            continue

    return dependencies


def fetch_dependencies(workshop_id, noisy=False):
    soup = fetch_page(workshop_id)
    if not soup:
        return {}

    main_author = extract_author(soup)
    dependencies = parse_dependencies(soup, noisy)

    return {"main_author": main_author, "dependencies": dependencies}
