import asyncio
import pymongo
import os
from dotenv import load_dotenv

# from undetected_playwright.async_api import async_playwright
from playwright.async_api import async_playwright
import asyncio
import subprocess

async def open_browser(page):
    # await page.set_viewport_size({'width': 1920, 'height': 1080})
    # await page.set_viewport_size({'width': 1600, 'height': 1080})
    await page.emulate_media(color_scheme='dark')
    # weblink="https://www.iaai.com"
    # weblink="https://www.iaai.com/LiveAuctionsCalendar"
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
        

async def fetch_live_auctions(browser , page, collection):
    live_auctions=[]

    while True:

        await page.reload(wait_until='load')
        await asyncio.sleep(30)

        all_auctions=await page.query_selector_all('a.btn.btn-green.joinsearch.small')
        
        if len(all_auctions)==0:
            await asyncio.sleep(300)
            print("No Auctions Found \nClosing the browser")
            await browser.close()
            # Clearing all data from collection
            collection.delete_many({"Info":"None"})
            break

        tasks=[get_links(auction,collection) for auction in all_auctions]
        await asyncio.gather(*tasks)

        await asyncio.sleep(2700)

async def main():
    async with async_playwright() as playwright:

        # args = []
        # disable navigator.webdriver:true flag
        # args.append("--disable-blink-features=AutomationControlled")
        # browser = await playwright.chromium.launch(args=args,headless=False)
        browser = await playwright.firefox.launch(headless=False)

        context = await browser.new_context()
        page = await context.new_page()
        await open_browser(page)
        await asyncio.sleep(5)
        await navigate_to_auctions(page)
        await asyncio.sleep(5)

        load_dotenv()
        client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        db = client['Copart']
        collection = db['AuctionLinks']

        # Clearing all data from collection
        collection.delete_many({})

        await fetch_live_auctions(browser,page,collection)

if __name__ == "__main__":
    asyncio.run(main())
