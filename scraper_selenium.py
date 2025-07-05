# Useful blog post: https://scrapfly.io/blog/posts/how-to-scrape-rightmove

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Function containing the scraping logic
def get_rightmove_data():
    """
    Scrapes property data from Rightmove using Selenium, with automatic driver
    management and correct, up-to-date selectors.
    """

    # Setup the Selenium WebDriver
    # Create a set of options for the Chrome browser
    options = webdriver.ChromeOptions()

    # This option helps prevent the "Chrome is being controlled" info bar from appearing
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Initialize the Chrome driver, letting Selenium handle the driver management automatically
    driver = webdriver.Chrome(options=options)

    # Define the base URL for our specific Cardiff property search
    base_url = "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=REGION%5E281&maxPrice=500000&minPrice=200000&radius=3.0&sortType=6"
    
    # Create an empty list to store the data for each property we scrape
    properties = []
    
    # Loop through a range of pages (10 is good for inital testing)
    for i in range(0, 2): 
        # Calculate the 'index' for each page (Rightmove uses multiples of 24 for pagination)
        index = i * 24
        # Construct the full URL for the specific page we want to scrape
        url = f"{base_url}&index={index}"
        
        print(f"Scraping page {i+1}...")

        # Tell the Selenium-controlled browser to navigate to the URL
        driver.get(url)

        # Use a try-except block to handle potential errors on any given page
        try:
            # HANDLE COOKIE BANNER (only on the first page) 
            if i == 0:
                # Use a nested try-except in case the banner doesn't appear
                try:
                    # Define the selector for the "Accept All" button
                    # Wait up to 5 seconds for the button to be clickable
                    accept_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
                    )

                    # Click the button to dismiss the banner
                    accept_button.click()
                    print("Cookie banner accepted.")

                    # Wait a moment for banner to disappear
                    time.sleep(1)
                except Exception:
                    print("Cookie banner not found or already accepted.")
            
            # Wait up to 10 seconds for at least one property card to be visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "PropertyCard_propertyCardContainer__VSRSA"))
            )
            
            # Get the entire HTML source of the page after JavaScript has loaded
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all the property card containers on the page
            listings = soup.find_all('div', class_='PropertyCard_propertyCardContainerWrapper__mcK1Z')

            # If no listings are found on a page, stop the scraper
            if not listings:
                print("No listings found on page, ending scrape.")
                break
            
            # Loop through all listings
            for listing in listings:
                # Use a try-except block to handle errors with individual cards
                try:
                    # Find the price element and get its text
                    price_element = listing.find('div', class_='PropertyPrice_price__VL65t')
                    price = price_element.text if price_element else 'N/A'

                    # Find the address element and get its text
                    address_element = listing.find('address', class_='PropertyAddress_address__LYRPq')
                    address = address_element.text if address_element else 'N/A'
                    
                    # Find the property link element and construct the full URL
                    card_link_element = listing.find('a', class_='propertyCard-link')
                    property_url = "https://www.rightmove.co.uk" + card_link_element['href'] if card_link_element and card_link_element.has_attr('href') else 'N/A'
                    
                    # Find the bedrooms element and get its text
                    bedrooms_element = listing.find('span', class_='PropertyInformation_bedroomsCount___2b5R')
                    bedrooms = bedrooms_element.text if bedrooms_element else 'N/A'

                    # Append the collected data as a dictionary to our main list
                    properties.append({
                        'price': price,
                        'address': address,
                        'bedrooms': bedrooms,
                        'url': property_url
                    })

                except Exception as e:
                    # If one card fails then continue with the others
                    print(f"Error parsing one listing: {e}")
                    continue

        except Exception as e:
            print(f"A major error occurred on page {i+1}: {e}")
            break

    print(f"\nFound {len(properties)} properties. Now fetching details for each...")
    
    # --- Visit Each Property URL for Detailed Features ---
    for prop in properties:
        # Check if the URL is valid before visiting
        if prop['url'] != 'N/A':
            print(f"Fetching details for: {prop['url']}")
            driver.get(prop['url'])
            try:
                # Wait for the key information section to be visible
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "_4hB3Hu-H_e-1PgonBvL0O"))
                )
                
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # Find bedrooms, bathrooms, and property type from the detail page
                # These selectors target the specific data attributes on the page
                bedrooms = detail_soup.find('div', {'data-testid': 'property-header-bedrooms'}).find('span').text
                bathrooms = detail_soup.find('div', {'data-testid': 'property-header-bathrooms'}).find('span').text
                property_type = detail_soup.find('p', class_='_1p2vUWq1IqtIYH3I5Rzyw6').text

                # Update the dictionary with the new data
                prop['bedrooms'] = bedrooms
                prop['bathrooms'] = bathrooms
                prop['property_type'] = property_type
                
                # Be polite to the server
                time.sleep(1)

            except Exception as e:
                print(f"Could not get details for {prop['url']}. Error: {e}")
                # If details can't be found, fill with N/A
                prop['bedrooms'] = 'N/A'
                prop['bathrooms'] = 'N/A'
                prop['property_type'] = 'N/A'
        
    
    # Close the browser window and end the Selenium session
    driver.quit()

    # Convert the list of dictionaries into a structured pandas DataFrame
    return pd.DataFrame(properties)

if __name__ == '__main__':
    print("Starting property data scrape...")

    # Call our main function to get the data
    df = get_rightmove_data()
    
    # Ensure DataFrame is not empty before trying to save it
    if not df.empty:
        # Save the DataFrame to a CSV file
        df.to_csv('cardiff_properties_final.csv', index=False)
        print(f"\n✅ Scraping complete! Found {len(df)} properties.")
        print("Data saved to cardiff_properties_final.csv")
        print("\n--- First 5 Properties ---")
        # Display the first 5 rows of the data
        print(df.head())
    else:
        print("\nNo properties were found. Please check for errors.")