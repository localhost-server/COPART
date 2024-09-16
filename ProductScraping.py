# from playwright.async_api import async_playwright
from playwright.async_api import async_playwright
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
        await new_page.goto(link)
        await asyncio.sleep(3)
    except Exception as e:
        await new_page.close()
        new_page = await context.new_page()
        await new_page.goto(link)
        await asyncio.sleep(3)

async def main():
    playwright = await async_playwright().start()
    args = ["--disable-blink-features=AutomationControlled"]
    browser = await playwright.firefox.launch(args=args, headless=True)#,proxy={'server': 'socks://localhost:9060'})
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
                Document = collection.find_one_and_update({"Info.Name":{"$exists":False},"Info":{"$ne":"processing"}}, {"$set": {"Info": "processing"}}, sort=[("creation_time", ASCENDING)])
                if not Document:
                    break

        carLink = Document['carLink']
        if "https://www.copart.com" not in carLink:
            collection.delete_one({"carLink": carLink})

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
                await asyncio.sleep(1.5)
                await visit(context,carLink, new_page)
            except TimeoutError:
                print("TimeoutError")
                continue

        MainInfo = OrderedDict()
        try:
            name_section = await new_page.query_selector('h1.title.my-0')
            name = await name_section.inner_text()
            MainInfo['Name'] = name
            type1=True
        except:
            try:
                name_section = await new_page.query_selector('h1.p-m-0')
                name = await name_section.inner_text()
                MainInfo['Name'] = name
                type1=False
            except:
                try:
                    if await new_page.is_visible('h2.subtitle-404'):
                        print("Maybe the car is sold")
                        # collection.update_one({"carLink": carLink}, {"$set": {"Info": "Car Sold Before Scraping"}})
                        collection.delete_one({"carLink": carLink})
                        passAll=True
                        continue
                    else:
                        collection.delete_one({"carLink": carLink})
                        continue
                except:
                    print("Nothing Found")
                    # collection.update_one({"carLink": carLink}, {"$set": {"Info": "Nothing Found"}})
                    collection.delete_one({"carLink": carLink})
                    passAll=True
                    continue
        if type1:
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
                            if await page.query_selector('a.btn.btn-sign-in'):
                                logged_out=True
                                break
                    except:
                        break
                    
                MainInfo['Vehicle Info'] = vehicle_info
            except:
                pass


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

        elif not type1:
            await new_page.click('span.p-ml-3.text-black')
            await asyncio.sleep(1)
            images_section = await new_page.query_selector_all('div.p-galleria-thumbnail-items-container')
            image_section = await images_section[1].query_selector('div.p-galleria-thumbnail-items')
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
                # Getting back
                await new_page.click('span.p-pl-3.text-dark-gray-3.p-fs-14')

            try:
                vehicle_info = OrderedDict()
                vinfo = await new_page.wait_for_selector('div.lot-details-section.vehicle-info')
                check = await vinfo.query_selector_all('div.lot-details-info')

                while check:
                    try:
                        label, value = (await check.pop(0).inner_text()).split("\n")
                        label = label.replace(":", "")
                        vehicle_info[label] = value
                        if "******" in value and "VIN" in label:
                            if await page.query_selector('a.btn.btn-sign-in'):
                                logged_out=True
                                break
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


        collection.update_one({"carLink": carLink}, {"$set": {"Info": MainInfo}})
        count += 1
        del Document

    await browser.close()
    await playwright.stop()

asyncio.run(main())
