from bs4 import BeautifulSoup
import requests
from pprint import pprint
from re import sub
from selenium import webdriver
import time

URL = "https://findalandtrust.org"
LAND_TRUST_PATH = "/land-trusts/explore/"


def snake_case(s):
    return "_".join(
        sub(
            "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))
        ).split()
    ).lower()


def parse_contact(soup):
    data = {
        "name": soup.find("div", {"class": "p-name"}).text.strip(),
        "street_address": soup.find("div", {"class": "p-street-address"}).text.strip(),
        "locality": soup.find("span", {"class": "p-locality"}).text.strip(),
        "postal_code": soup.find("span", {"class": "p-postal-code"}).text.strip(),
        "region": soup.find("span", {"class": "p-region"}).text.strip(),
    }

    sidebar_links = soup.find("div", {"class": "sidebar"}).find_all("a")
    phone = [x["href"] for x in sidebar_links if x["href"].startswith("tel:")][0]
    email = [
        x["href"] for x in sidebar_links if x["href"].startswith("mailto:")
    ]  # These rat bastards are protecting the email so I can't get it

    data["phone"] = phone

    return data


def parse_demographics(soup):
    data = {}
    rows = soup.find("ul", {"class": "list mt-3"}).find_all("li")
    for row in rows:
        k = row.find("div", {"class": "label"}).text.strip()
        v = row.find("div", {"class": "rich-text body"}).text.strip()
        data[snake_case(k)] = v

    return data


def parse_features(soup):
    features = soup.find_all(
        "div",
        {
            "class": "item item-attribute mt-6 has-icon orientation-horizontal size-small"
        },
    )
    data = [f.find("header").text.strip() for f in features]
    return data


def parse_profile(id=None, path=None):
    data = {}
    if id:
        endpoint = URL + LAND_TRUST_PATH + str(id)
    if path:
        endpoint = URL + path
        id = path.split("/")[2]
    print(endpoint)

    data["id"] = endpoint.split("/")[-1]
    data["url"] = endpoint

    try:
        response = requests.get(endpoint)
        response.raise_for_status

        soup = BeautifulSoup(response.content, "html.parser")

        name = soup.find("h1", {"class": "title"}).text.strip()
        data["name"] = name
    except:
        return data

    try:
        data["contact"] = parse_contact(soup)
    except:
        pass

    try:
        data["demographics"] = parse_demographics(soup)
    except:
        pass

    try:
        data["features"] = parse_features(soup)
    except:
        pass

    return data


def get_land_trusts():
    endpoint = URL + LAND_TRUST_PATH
    nearby = "nearby=false"
    iter_endpoint = endpoint + "?" + nearby
    page = 1

    # Must create a selenium browser because the content is loaded after page load with javascript
    browser = webdriver.Firefox()

    empty_response = False  # Loop exit condition

    data = []  # Return object

    while not empty_response:
        print(iter_endpoint)

        # Get page and wait for load
        browser.get(iter_endpoint)
        time.sleep(1)

        # Load page contents
        soup = BeautifulSoup(browser.page_source, "html.parser")

        # Find all links to land trusts
        land_trusts = soup.find("div", {"class": "site container"}).find_all(
            "a", href=True
        )
        land_trusts = [x["href"] for x in land_trusts]
        land_trusts = set([x for x in land_trusts if x.startswith(LAND_TRUST_PATH)])

        # Aggregate results
        data += land_trusts
        # Exit if no land trusts were found
        empty_response = len(land_trusts) == 0

        # Get next page
        page += 1
        iter_endpoint = endpoint + "?" + f"page={page}" + "&" + nearby

    return data


headers = "\t".join(
    [
        "id",
        "url",
        "name",
        "name",
        "street_address",
        "locality",
        "region",
        "postal_code",
        "adopted_2017_standards_&_practices",
        "number_of_board_members",
        "number_of_full_time_staff",
        "number_of_supporters",
        "number_of_volunteers",
        "year_first_joined",
        "features",
    ]
)


def convert_to_csv(trust_info):
    return "\t".join(
        [
            trust_info.get("id"),
            trust_info.get("url"),
            trust_info.get("name", ""),
            trust_info.get("contact", {}).get("name", ""),
            trust_info.get("contact", {}).get("street_address", ""),
            trust_info.get("contact", {}).get("locality", ""),
            trust_info.get("contact", {}).get("region", ""),
            trust_info.get("contact", {}).get("postal_code", ""),
            trust_info.get("demographics", {}).get(
                "adopted_2017_standards_&_practices", ""
            ),
            trust_info.get("demographics", {}).get("number_of_board_members", ""),
            trust_info.get("demographics", {}).get("number_of_full_time_staff", ""),
            trust_info.get("demographics", {}).get("number_of_supporters", ""),
            trust_info.get("demographics", {}).get("number_of_volunteers", ""),
            trust_info.get("demographics", {}).get("year_first_joined", ""),
            "|".join(trust_info.get("features", [])),
        ]
    )


def main():
    data = []

    # Get paths to all land trusts on page
    land_trusts = get_land_trusts()
    print(f"Number of land trusts found: {len(land_trusts)}")

    # Get land trust info from path
    for land_trust in land_trusts:
        info = parse_profile(path=land_trust)
        data.append(info)

    # pprint(data)

    # Write CSV
    with open("land_trust.csv", "w") as file:
        file.write(headers + "\n")
        for d in data:
            file.write(convert_to_csv(d) + "\n")


if __name__ == "__main__":
    main()
