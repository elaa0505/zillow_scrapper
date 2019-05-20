from input_automation import InputAutomator
from time import sleep
from re import search
import requests

# General Settings
file_name = "listings.csv"

travel_modes = ("transit", "driving")

# Specific Settings
maps_key = ""

destination = ()

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
    "latitude": r'"latitude":([-\d\.]+)',
    "longitude": r'"longitude":([-\d\.]+)',
}

vars_to_scrape = tuple(patterns.keys())     # forces fixed order
vars_to_calc = tuple(["distance" + mode for mode in travel_modes] + ["duration" + mode for mode in travel_modes])
all_vars = vars_to_scrape + vars_to_calc
output_data = []

try:
    with open(file_name, "r") as input_file:
        varlist = [var.strip() for var in input_file.readline().split(",")]    # skip last comma
        assert set(all_vars) == set(varlist), "Loaded file does not contain the same vars as scrapper"
        for line in input_file:
            data = [key.strip() for key in line.split(",")]
            new_obs = dict(zip(varlist, data))
            output_data.append(new_obs)
except FileNotFoundError as e:
    print("Error loading data, continuing.")
except AssertionError as e:
    print(e)


def get_travel(listing):
    lat, long = listing["latitude"], listing["longitude"]
    for travel_mode in travel_modes:
        req_url = f"https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?origins={lat},{long}&destinations=" \
            f"{destination[0]},{destination[1]}&travelMode={travel_mode}&key={maps_key}"
        req = requests.get(req_url)
        res = req.json()
        listing["distance"+travel_mode] = res["resourceSets"][0]["resources"][0]["results"][0]["travelDistance"]
        listing["duration"+travel_mode] = res["resourceSets"][0]["resources"][0]["results"][0]["travelDuration"]
    return


def get_listings(raw_source):
    valid_listings = []
    listings = raw_source.split('"detailUrl":')[1:]     # first index is garbage data
    for listing in listings:
        new_listing = dict.fromkeys(all_vars)
        for var in vars_to_scrape:
            try:
                new_listing[var] = search(patterns[var], listing).group(1).replace(",", " ")
                if var == "price":
                    new_listing[var] = new_listing[var].replace(" ", "")
            except (AttributeError, IndexError):
                new_listing[var] = None

        if new_listing["latitude"] is not None and new_listing["longitude"] is not None:
            print("Getting travel data.")
            get_travel(new_listing)

        if not (None in new_listing.values() or "null" in new_listing.values()):    # Zillow may return "null"
            if not new_listing["listing_id"] in set([listing["listing_id"] for listing in output_data]):
                valid_listings.append(new_listing)
                output_file.write(' ,'.join(['{}'] * len(all_vars)).format(
                    *["{" + var + "}" for var in all_vars]).format(**new_listing) + "\n")
    return valid_listings


with open(file_name, "w") as output_file:
    header = ' ,'.join(['{}'] * len(all_vars)).format(*all_vars)
    output_file.write(header + '\n')

    driver = None

    for zipcode in (str(zipcode) for zipcode in zipcodes):
        if driver:
            driver.quit()  # Keeps IE from crashing

        driver = InputAutomator()

        driver.get('https://www.zillow.com/homes/for_rent/')
        print(f"Working on {zipcode}.")

        driver.wait_for("class", "react-autosuggest__input")
        driver.move_to("class", "react-autosuggest__input", x_offset=40)
        attempts = 0
        while not driver.wait_for("class", "react-autosuggest__suggestions-list", timeout=1):
            driver.click()
            if attempts > 10:
                break
            else:
                attempts += 1
        driver.type("^a{Del}")
        sleep(1)
        driver.type(zipcode)
        sleep(1)
        driver.type("{Enter}")
        sleep(1)
        # Check if no results were found for search
        print(f"Checking for 'No results found'.")
        if driver.wait_for("class", "zsg-notification-bar", timeout=5):
            continue
        print(f"Waiting for results to load.")
        page_num = 1
        while driver.wait_for("class", "result-count"):
            print(f"Getting listings on page {page_num}")
            valid_listings = get_listings(driver.page_source)
            output_data.extend(valid_listings)
            driver.move_to("class", "result-count")
            sleep(3)
            print(f"Scrolling down and looking for 'Next' button.")
            driver.scroll("down", 30)
            # Check if we are on the last page
            if not (driver.wait_for("class", "zsg-pagination-next", timeout=5) and driver.find_element_by_class_name("zsg-pagination-next").text == "NEXT"):
                print(f"Finished with {zipcode}.")
                break
            driver.move_to("class", "zsg-pagination-next", x_offset=15)
            driver.click()
            sleep(3)
            page_num += 1
            print(f"Clicked next button, moving onto {page_num}")

    print(f"All done!")
    driver.quit()
