from bs4 import BeautifulSoup
import requests
from pprint import pprint

URL = "https://findalandtrust.org/"
LAND_TRUST_PATH = "land_trusts/"
STATE_PATH = "states/"
STATE_IDS = [
    "virginia51",
    "colorado8",
    "utah49"
]

def parse_contact(table):
    data = {}
    rows = table.find_all("tr")
    name = rows[0].text.strip()
    cols = rows[1].find_all("td")
    address = cols[0].text.strip()
    data["address"] = address
    contact = cols[1].text.strip()
    split_contact = contact.split("\n")
    for c in split_contact:
        key, val = c.split(":")
        data[key.strip()] = val.strip()
    return data

def parse_demographics(table):
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        key = row.find("th").text.strip()
        val = row.find("td").text.strip()
        data[key] = val
    return data

def parse_acres(table): 
    data = []
    rows = table.find_all("tr")
    keys = [th.text.strip() for th in rows[0].find_all("th")]
    for row in rows[1:]:
        vals = [td.text.strip() for td in row.find_all("td")]
        data.append(dict(zip(keys, vals)))
    return data

def parse_counties(div):
    data = []
    states = div.find_all("p", {"class": "counties_header"})
    states = [state.text.strip()[:-1] for state in states]
    
    counties = []
    county_lists = div.find_all("div", {"class": "counties_list"})
    for county_list in county_lists:
        counties.append([county.text.strip() for county in county_list.find_all("a")])
        
    return dict(zip(states, counties))

def parse_profile(id = None, path = None):
    data = {}
    if id:
        endpoint = URL + LAND_TRUST_PATH + str(id)
    if path:
        endpoint = URL + path
        id = path.split("/")[2]
    print(endpoint)
    
    response = requests.get(endpoint)
    response.raise_for_status
    
    soup = BeautifulSoup(response.content, "html.parser")

    data["id"] = id
    
    name = soup.find("div", {"class":"top_header"}).find("h2").text.strip()
    data["name"] = name
    
    try:
        contact_raw = soup.find("div", {"class":"contact_bg"}).find("table")
        contact = parse_contact(contact_raw)
        data["contact"] = contact
    except:
        pass
    
    try:
        demographics_raw = soup.find("div", {"class":"demographics_bg"}).find("table")
        demographics = parse_demographics(demographics_raw)
        data["demographics"] = demographics
    except:
        pass
    
    try:
        acres_raw = soup.find("div", {"class":"acres_bg"}).find("table")
        acres = parse_acres(acres_raw)
        data["acres"] = acres
    except:
        pass
    
    try:
        counties_raw = soup.find("div", {"class":"counties_bg"})
        counties = parse_counties(counties_raw)
        data["counties"] = counties
    except:
        pass
    
    return data
    
def get_land_trut_paths_by_state_id(id):
    endpoint = URL + STATE_PATH + str(id) + "/" + LAND_TRUST_PATH
    print(endpoint)
    
    response = requests.get(endpoint)
    response.raise_for_status
    
    soup = BeautifulSoup(response.content, "html.parser")
    land_trusts = soup.find("table", {"class": "land_trusts"})
    
    return [a["href"] for a in land_trusts.find_all("a", href=True)]
        
        
def main():
    data = {}

    for state_id in STATE_IDS:
        paths = get_land_trut_paths_by_state_id(state_id)
        for path in paths:
            profile = parse_profile(path = path)
            data[profile["id"]] = profile
    pprint(data)
    
if __name__ == "__main__":
    main()