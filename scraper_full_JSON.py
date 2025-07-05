#TO SEE THE FULL JSON OF THE PROPERTY:

import requests
import json
import pandas as pd
import time
from bs4 import BeautifulSoup

def find_property_list(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'properties' and isinstance(value, list) and value:
                if 'price' in value[0] and 'bedrooms' in value[0]:
                    return value
            result = find_property_list(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_property_list(item)
            if result:
                return result
    return None

def get_rightmove_data():
    base_url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E281&maxPrice=500000&minPrice=200000&radius=3.0&sortType=6"
    properties = []

    # We only need to fetch the first page to inspect the data
    url = f"{base_url}&index=0"
    
    print(f"Fetching data from page 1 to inspect features...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve page. Status code: {response.status_code}")
        return pd.DataFrame() # Return empty DataFrame on failure

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        data_script = soup.find('script', id='__NEXT_DATA__')
        
        if not data_script:
            print("Could not find the __NEXT_DATA__ script tag on this page.")
            return pd.DataFrame()

        data = json.loads(data_script.string)
        property_list = find_property_list(data)

        if not property_list:
            print("Could not find property list in data layer.")
            return pd.DataFrame()

        # --- NEW CODE TO DISPLAY ALL DATA FOR THE FIRST PROPERTY ---
        # Get the very first property from the list
        first_property_data = property_list[0]
        
        # Print a header
        print("\n✅ --- All Available Data for the First Property --- ✅\n")
        
        # Use json.dumps to "pretty-print" the dictionary with indentation
        print(json.dumps(first_property_data, indent=4))
        
        print("\n--- End of Data ---")
        
        # The script will now stop after printing the data for one property.
        # This is so you can review the available features.
        
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        
    # Return an empty DataFrame because we are only inspecting data, not collecting it
    return pd.DataFrame()


if __name__ == '__main__':
    get_rightmove_data()

