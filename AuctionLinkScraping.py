import asyncio
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
from playwright.async_api import async_playwright

# Setting CDT timezone
cdt = pytz.timezone('America/Chicago')

async def open_browser(page):
    await page.emulate_media(color_scheme='dark')
    weblink = "https://www.copart.com/login/"
    await page.goto(weblink, wait_until='load')
    await asyncio.sleep(20)
    # Find the email input field by its ID
    email_input = await page.query_selector('#username')
    email = "matti19913@gmail.com"
    await email_input.fill(email)
    password_input = await page.query_selector('#password')
    # Enter the desired content
    password = "Copart2023!"
    await password_input.fill(password)
    # Clicking on the remember me checkbox
    await page.click('text=Remember?')
    # Clicking on the login button
    await page.click('text=Sign Into Your Account')
    # Waiting for the page to load
    await asyncio.sleep(5)
    return page

async def navigate_to_auctions(page):
    await page.goto("https://www.copart.com/todaysAuction")

async def get_links(auction, collection):
    try:
        link_element = await auction.get_attribute('href')
        relative_url = link_element.lstrip('.')
        whole_url = "https://www.copart.com" + relative_url

        if collection.find_one({'link': whole_url}) is None:
            print(f"Inserting URL {whole_url}")
            collection.insert_one({'link': whole_url, 'Info': "None"})
    except Exception as e:
        print(e)

async def fetch_live_auctions(playwright, collection):

    while datetime.now(cdt).strftime("%H:%M") < "23:30":
        try:
            print(f"Time: {datetime.now(cdt).strftime('%H:%M')}, Launching browser...")

            # Delete completed auctions before each round of checks
            collection.delete_many({"Info": "done"})
            print("Removed auctions marked as 'done'.")

            browser = await playwright.firefox.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await navigate_to_auctions(page)
            await asyncio.sleep(5)

            check_count = 0  # Counter to track 5 checks
            while check_count < 5:
                print(f"Checking for auctions, attempt {check_count + 1}/5.")
                all_auctions = await page.query_selector_all('a.btn.btn-green.joinsearch.small')

                if len(all_auctions) == 0:
                    print("No auctions found on this attempt.")
                else:
                    print(f"Found {len(all_auctions)} auctions, scraping links...")
                    tasks = [get_links(auction, collection) for auction in all_auctions]
                    await asyncio.gather(*tasks)

                check_count += 1
                await asyncio.sleep(60)  # Wait 1 minute between checks (5-minute span)

            # After 5 checks, close the browser
            print("Closing browser after 5 checks, waiting 30 minutes before checking again.")
            await page.close()
            await context.close()
            await browser.close()
            await asyncio.sleep(60 * 30)  # Wait 30 minutes before starting the next round of checks

        except Exception as e:
            print(f"Error occurred: {e}")
            await browser.close()
            await asyncio.sleep(30)  # Sleep briefly before retrying

    print("Time passed 23:30, closing the script.")
    # Delete entries with "None" info before ending the script
    collection.delete_many({"Info": "None"})

async def main():
    async with async_playwright() as playwright:
        load_dotenv()
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client['Copart']
        collection = db['AuctionLinks']
        
        # Clearing all data from collection
        collection.delete_many({})
        await fetch_live_auctions(playwright, collection)

if __name__ == "__main__":
    asyncio.run(main())
