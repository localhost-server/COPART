import asyncio
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz
# from undetected_playwright.async_api import async_playwright
from playwright.async_api import async_playwright
import asyncio
import subprocess

# Setting CDT timezone
cdt=pytz.timezone('America/Chicago')

async def open_browser(page):
    await page.emulate_media(color_scheme='dark')
    weblink="https://www.copart.com/login/"
    await page.goto(weblink, wait_until='load')
    await asyncio.sleep(20)
    # Find the email input field by its ID
    email_input = await page.query_selector('#username')
    # Enter the desired content
    email = "matti19913@gmail.com"
    await email_input.fill(email)
    password_input = await page.query_selector('#password')
    # Clear the existing value (if any)
    await password_input.fill('')
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

async def get_links(auction,collection):
    try:
        link_element = await auction.get_attribute('href')
        relative_url = link_element.lstrip('.')
        whole_url = "https://www.copart.com"+relative_url

        if collection.find_one({'link': whole_url}) is None:
            print(f"Inderting URL {whole_url}")
            # Upload the link to MongoDB
            collection.insert_one({'link': whole_url, 'Info': "None"})
    except Exception as e:
        print(e)
        

async def fetch_live_auctions(playwright , collection):

    while datetime.now(cdt).strftime("%H:%M")<="23:30":
        try:
            browser = await playwright.firefox.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            # await open_browser(page)
            await asyncio.sleep(5)
            await navigate_to_auctions(page)
            await asyncio.sleep(5)
    
            await page.reload()
            await asyncio.sleep(10)
            
            # deleting all the data from the collection where Info is done
            collection.delete_many({"Info":"done"})
            print(f'Time : {datetime.now(cdt).strftime("%H:%M")}')
            for i in range(5):
                all_auctions=await page.query_selector_all('a.btn.btn-green.joinsearch.small')
                if len(all_auctions)==0:
                    print("No Auctions Found \n")
                    await asyncio.sleep(60*10)
                    break
                else:
                    tasks=[get_links(auction,collection) for auction in all_auctions]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(300)
    
            print("Closing the page and context")
            await page.close()
            await context.close()
        except:
            # added exception later if though to remove it then remove it
            await browser.close()
            await asyncio.sleep(30)
            await fetch_live_auctions(playwright,collection)

    # Will check after an hour
    await asyncio.sleep(60*60)

    print("Closing the browser")
    await asyncio.sleep(20)
    await browser.close()
    # Clearing all data from collection
    collection.delete_many({"Info":"None"})

async def main():
    async with async_playwright() as playwright:

        load_dotenv()
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client['Copart']
        collection = db['AuctionLinks']

        # Clearing all data from collection
        # collection.delete_many({})

        await fetch_live_auctions(playwright,collection)

if __name__ == "__main__":
    asyncio.run(main())
