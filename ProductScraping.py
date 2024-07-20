# from playwright.async_api import async_playwright
from undetected_playwright.async_api import async_playwright
import time
import asyncio
import subprocess
from collections import OrderedDict
import pymongo
from pymongo import ASCENDING
import os
import json
import re
from dotenv import load_dotenv

async def open_browser(page):
    await page.emulate_media(color_scheme='dark')
    weblink = "https://www.copart.com/login/"
    await page.goto(weblink, wait_until='load')
    return page

async def visit(context,link, new_page):
    try:
        await new_page.goto(link, wait_until='load')
        await asyncio.sleep(3)
    except Exception as e:
        await new_page.close()
        new_page = await context.new_page()
        await new_page.goto(link, wait_until='load')
        await asyncio.sleep(3)

async def main():
    playwright = await async_playwright().start()
    args = ["--disable-blink-features=AutomationControlled"]
    browser = await playwright.chromium.launch(args=args, headless=False)#,proxy={'server': 'socks://localhost:9060'})
    # browser = await playwright.chromium.launch(args=args, headless=False,proxy={'server': 'http://localhost:8080'})
    context = await browser.new_context()
    page = await context.new_page()
    await open_browser(page=page)
    await asyncio.sleep(5)

    # Find the email input field by its ID
    email_input = await page.query_selector('#username')
    email = "matti19913@gmail.com"
    await email_input.fill(email)

    password_input = await page.query_selector('#password')
    await password_input.fill('')
    password = "Copart2023!"
    await password_input.fill(password)

    await page.click('text=Remember?')
    await page.click('text=Sign Into Your Account')
    await asyncio.sleep(5)

    load_dotenv()
    client = pymongo.MongoClient(os.getenv("MONGO_URI"))
    db = client['Copart']
    collection = db['Cars']
    new_page = await context.new_page()

    count = 0

    while True:
        Document = collection.find_one_and_update({"Info": "None"}, {"$set": {"Info": "processing"}}, sort=[("creation_time", ASCENDING)])

        logged_out = False
        
        if not Document:
            await asyncio.sleep(3)
            Document = collection.find_one_and_update({"Info": "processing"}, {"$set": {"Info": "processing"}}, sort=[("creation_time", ASCENDING)])
            if not Document:
                break

        carLink = Document['carLink']

        link = carLink.replace("https://www.copart.com", "")
        print(link)

        if count > 70:
            count=0
            print("Closing the browser after 100 cars")
            await new_page.close()
            new_page = await context.new_page()
            await asyncio.sleep(30)
            await visit(context,carLink, new_page)
        else:
            try:
                await visit(context,carLink, new_page)
            except TimeoutError:
                print("TimeoutError")
                continue

        MainInfo = OrderedDict()
        try:
            name_section = await new_page.query_selector('h1.title.my-0')
            name = await name_section.inner_text()
            MainInfo['Name'] = name
        except:
            if await new_page.is_visible('h2.subtitle-404'):
                print("Maybe the car is sold")
                collection.update_one({"carLink": carLink}, {"$set": {"Info": "Car Sold Before Scraping"}})
                continue

        image_section = await new_page.query_selector('.d-flex.thumbImgContainer')
        if image_section:
            images = await image_section.query_selector_all('img')
            image_urls = [await image.get_attribute('src') for image in images]
            image_urls = [url.replace("thb", "ful") for url in image_urls]

            image_names = []
            for i in image_urls:
                numeric_part = re.search(r'\d+', link).group()
                ImageName = f'{name}-{numeric_part}-{image_urls.index(i)}.jpg'
                image_names.append(ImageName)
            print("Images Found")
            subprocess.Popen(["python", "downloadNupload.py", name, link, json.dumps(image_urls)])
            
            MainInfo['Images'] = image_names

        try:
            vehicle_info = OrderedDict()
            vinfo = await new_page.wait_for_selector('div.panel-content.d-flex.f-g1.d-flex-column.full-width')
            vinfo = await vinfo.query_selector('div.f-g2')
            check = await vinfo.query_selector_all('div.d-flex')
    
            while check:
                try:
                    label, value = (await check.pop(0).inner_text()).split("\n")
                    label = label.replace(":", "")
                    vehicle_info[label] = value
                    if "******" in value and "VIN" in label:
                        logged_out=True
                        # break
                except:
                    break
                
            MainInfo['Vehicle Info'] = vehicle_info
        except:
            pass

        if logged_out:
            collection.update_one({"carLink": carLink}, {"$set": {"Info": "None"}})
            if await page.query_selector("a.btn.btn-sign-in"):  
                weblink = "https://www.copart.com/login/"
                await page.goto(weblink, wait_until='load')
                await asyncio.sleep(5)
    
                # Find the email input field by its ID
                email_input = await page.query_selector('#username')
                email = "matti19913@gmail.com"
                await email_input.fill(email)
    
                password_input = await page.query_selector('#password')
                await password_input.fill('')
                password = "Copart2023!"
                await password_input.fill(password)
    
                await page.click('text=Remember?')
                await page.click('text=Sign Into Your Account')
                await asyncio.sleep(30)
                logged_out=False
                continue


        try:
            sale_info = OrderedDict()
            sinfo = await new_page.wait_for_selector("div.panel.clr.overflowHidden")
            # sinfo = await new_page.query_selector("div.panel.clr.overflowHidden")
            check = await sinfo.query_selector_all('div.d-flex')
    
            while check:
                try:
                    data = await check.pop(0).inner_text()
                    if "\n\n" in data:
                        label, value = data.split("\n\n")
                        label = label.replace(":", "")
                    elif "\n" in data:
                        label, value = data.split("\n", 1)
                        label = label.replace(":", "")
                except:
                    break
                sale_info[label] = value
    
            MainInfo['Sale Info'] = sale_info
        except:
            pass
        collection.update_one({"carLink": carLink}, {"$set": {"Info": MainInfo}})
        count += 1
        del Document

    await browser.close()
    await playwright.stop()

asyncio.run(main())
