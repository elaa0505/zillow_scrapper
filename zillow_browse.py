from input_automation import InputAutomator
from time import sleep
from re import search

file_name = "listings.csv"

zipcodes = {}

vars_to_scrape = ['listing_id', 'address', 'price', 'sqft', 'beds', 'baths', 'home_type', 'url']

patterns = {
    "listing_id": r'"zpid":([\d]+,)',
    "price": r'"price":"\$([\d,]+)',
    "address": r'"address":"([\w ,]+)',
    "sqft": r'"area":([\w]+)',
    "beds": r'"beds":([\w\.]+)',
    "baths": r'"baths":([\w\.]+)',
    "home_type": r'"homeType":"([\w]+)',
    "url": r'^"([\w:\/\.-]+)",',
}


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
            except AttributeError:
                new_obs[var] = None

            if not (None in new_obs.values() or "null" in new_obs.values()):
                output.append(new_obs)
    return output

driver = InputAutomator()

output_data = []
for zip in zipcodes:
    driver.get('https://www.zillow.com/homes/for_rent/')

    driver.wait_for("class", "zsg-searchbox-content-container")
    driver.move_to("class", "zsg-searchbox-content-container", x_offset=-40)
    sleep(1)
    driver.click()
    sleep(1)
    driver.type("^a{Del}")
    driver.type(zip)
    driver.type("{Enter}")
    sleep(1)
    # Check if no results were found for search
    if driver.wait_for("css", ".zoom-out-message", timeout=5) or driver.wait_for("class", "zsg-icon-x-thick", timeout=5):
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
