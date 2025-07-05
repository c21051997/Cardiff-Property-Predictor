import requests
import json
import pandas as pd
import time
from bs4 import BeautifulSoup

def find_property_list(data):
    """
    Recursively searches a dictionary or list for a key named 'properties'
    that contains a list of property-like objects.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'properties' and isinstance(value, list) and value:
                # Check if the list items look like properties before returning
                if 'price' in value[0] and 'bedrooms' in value[0]:
                    return value
            
            # Recurse into nested dictionaries
            result = find_property_list(value)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            # Recurse into items in a list
            result = find_property_list(item)
            if result:
                return result
    return None

def get_rightmove_data():
    """
    Scrapes a comprehensive set of property data from Rightmove's hidden JSON data layer.
    """
    base_url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E281&maxPrice=500000&minPrice=200000&radius=3.0&sortType=6"
    properties = []

    # Scrape 70 pages to get a large dataset
    for i in range(0, 70):
        index = i * 24
        url = f"{base_url}&index={index}"
        
        print(f"Fetching data from page {i+1}...")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page {i+1} (Status: {response.status_code}). This likely means it's the last page. Stopping scrape.")
            break

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            data_script = soup.find('script', id='__NEXT_DATA__')
            
            if not data_script:
                print("Could not find the __NEXT_DATA__ script tag on this page.")
                continue

            data = json.loads(data_script.string)
            property_list = find_property_list(data)

            if not property_list:
                print("No more properties found in data layer. Ending scrape.")
                break

            for prop in property_list:
                # Use .get() for safe access to nested dictionary keys
                location = prop.get('location', {})
                price = prop.get('price', {})
                tenure = prop.get('tenure', {})
                listing_update = prop.get('listingUpdate', {})

                # Append all the desired features to our list
                properties.append({
                    # Essential Features
                    'price': price.get('amount'),
                    'bedrooms': prop.get('bedrooms'),
                    'bathrooms': prop.get('bathrooms'),
                    'latitude': location.get('latitude'),
                    'longitude': location.get('longitude'),
                    # Recommended Features
                    'property_type': prop.get('propertySubType', 'N/A'),
                    'tenure': tenure.get('tenureType'),
                    # Advanced Features
                    'listing_update_reason': listing_update.get('listingUpdateReason'),
                    'summary': prop.get('summary'),
                    # Other Useful Info
                    'url': "https://www.rightmove.co.uk" + prop.get('propertyUrl', '')
                })

        except Exception as e:
            print(f"An error occurred while parsing page {i+1}: {e}")
            continue
        
        time.sleep(0.5)
            
    return pd.DataFrame(properties)


if __name__ == '__main__':
    print("Starting property data scrape...")
    df = get_rightmove_data()
    
    if not df.empty:
        # Save the final, enriched dataset
        df.to_csv('model/cardiff_properties_enriched.csv', index=False)
        print(f"\n✅ Scraping complete! Found {len(df)} properties.")
        print("Data saved to cardiff_properties_enriched.csv")
    else:
        print("\nNo properties were found.")