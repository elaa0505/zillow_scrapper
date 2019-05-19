from input_automation import InputAutomator
from time import sleep
from re import search
from math import sin, cos, sqrt, atan2, radians


file_name = "listings.csv"

zipcodes = {}

patterns = {
    "listing_id": r'"zpid":([\d]+,)',
    "price": r'"price":"\$([\d,]+)',
    "address": r'"address":"([\w ,]+)',
    "sqft": r'"area":([\w]+)',
    "beds": r'"beds":([\w\.]+)',
    "baths": r'"baths":([\w\.]+)',
    "home_type": r'"homeType":"([\w]+)',
    "url": r'^"([\w:\/\.-]+)",',
    "latitude": r'"latitude":([-\d\.]+),',
    "longitude": r'"longitude":([-\d\.]+),',
    "distance": r''
}

vars_to_scrape = patterns.keys()
output_data = []


try:
    with open(file_name, "r") as input_file:
        varlist = [var.strip() for var in input_file.readline().split(",")]    # skip last comma
        assert set(vars_to_scrape) == set(varlist), "Loaded file does not contain the same vars as scrapper"
        for line in input_file:
            data = [key.strip() for key in line.split(",")]
            new_obs = dict(zip(varlist, data))
            output_data.append(new_obs)
except FileNotFoundError as e:
    print("Error loading data, continuing.")
except AssertionError as e:
    print(e)


def get_distance(lat, long):
    R = 6373.0
    lat1 = radians(float(lat))
    lon1 = radians(float(long))
    lat2 = radians(32.8662187)
    lon2 = radians(-117.2499748)
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance * 0.621371  # convert to miles because 'merica


def get_listings(raw_source):
    output = []
    listings = raw_source.split('"detailUrl":')[1:]
    for listing in listings:
        new_obs = dict.fromkeys(vars_to_scrape)

        for var in vars_to_scrape:
            try:
                new_obs[var] = search(patterns[var], listing).group(1).replace(",", " ")
                if var == "price":
                    new_obs[var] = new_obs[var].replace(" ", "")
            except (AttributeError, IndexError):
                new_obs[var] = None

            if new_obs["latitude"] is not None and new_obs["longitude"] is not None and var == "distance":
                new_obs["distance"] = get_distance(new_obs["latitude"], new_obs["longitude"])

            if not (None in new_obs.values() or "null" in new_obs.values()):
                output.append(new_obs)
    return output


driver = InputAutomator()

zipcodes = [str(zipcode) for zipcode in zipcodes]

for zipcode in zipcodes:
    driver.get('https://www.zillow.com/homes/for_rent/')

    driver.wait_for("class", "zsg-searchbox-content-container")
    driver.move_to("class", "zsg-searchbox-content-container", x_offset=-40)
    sleep(1)
    driver.click()
    sleep(1)
    driver.type("^a{Del}")
    driver.type(zipcode)
    driver.type("{Enter}")
    sleep(1)
    # Check if no results were found for search
    if driver.wait_for("class", "zsg-notification-bar", timeout=5):
        continue
    while driver.wait_for("class", "result-count"):
        new_listings = get_listings(driver.page_source)
        output_data.extend(new_listings)
        driver.move_to("class", "result-count")
        sleep(3)
        driver.scroll("down", 30)
        # Check if we are on the last page
        if not (driver.wait_for("class", "zsg-pagination-next", timeout=5) and driver.find_element_by_class_name("zsg-pagination-next").text == "NEXT"):
            break
        driver.move_to("class", "zsg-pagination-next", x_offset=15)
        driver.click()
        sleep(3)

# Get unique listings
output_data = list({val['listing_id']: val for val in output_data}.values())

with open(file_name, "w") as output_file:
    header = ' ,'.join(['{}']*len(vars_to_scrape)).format(*vars_to_scrape)
    output_file.write(header + '\n')
    for listing in output_data:
        output_file.write("{listing_id}, {address}, {price}, {sqft}, {beds}, {baths}, {home_type}, {url}\n".format(**listing))
