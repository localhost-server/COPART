from playwright.async_api import async_playwright
import asyncio
import time
import pymongo
from pymongo import ASCENDING
import os
from dotenv import load_dotenv
import json
import subprocess
import random

load_dotenv()

# reading extensionid.txt
with open("extensionid.txt", "r") as file:
    extension_id = file.read()

async def open_browser(page):
    await page.emulate_media(color_scheme='dark')
    weblink = "https://www.iaai.com/Login/ExternalLogin?ReturnUrl=%2FDashboard%2FDefault"
    await page.goto(weblink, wait_until='load')
    await asyncio.sleep(5)
    return page

async def visit(context,link, newPage):
    try:
        await newPage.goto(link, wait_until='load')
        await asyncio.sleep(1)
    except Exception as e:
        await newPage.close()
        newPage = await context.new_page()
        await newPage.goto(link, wait_until='load')
        await asyncio.sleep(1)

async def main():
    playwright = await async_playwright().start()
    args = [f"--disable-extensions-except=./Capsolver",
    f"--load-extension=./Capsolver","--disable-blink-features=AutomationControlled"]
    # username = os.getenv("OxylabUser")
    # passwd = os.getenv("OxylabPass")
    username = os.getenv("BDUser")
    passwd = os.getenv("BDPass")
    useProxy= os.getenv("USEPROXY")
    # num=random.randint(1,21)
    # if num<10:
    #     proxy = f'isp.oxylabs.io:800{num}'
    # else:
    #     proxy = f'isp.oxylabs.io:80{num}'
    proxy = f'brd.superproxy.io:22225'
    print(proxy)

    if useProxy == "True":
        browser = await playwright.chromium.launch_persistent_context('',args=args, headless=False,proxy={
                "server": proxy,
                "username": username,
                "password": passwd
                })
    elif useProxy == "False":
        browser = await playwright.chromium.launch_persistent_context('',args=args, headless=False)

    # context = await browser.new_context(proxy={
    #         "server": proxy,
    #         "username": username,
    #         "password": passwd
    #         }) #{"server": "socks5://127.0.0.1:9051"})
    context = browser
    page =  await context.new_page()
    # Enabling the extension for incognito mode
    # await page.goto(f"chrome://extensions/?id={extension_id}")
    # await asyncio.sleep(3)
    # await page.mouse.click(640,640)
    # await asyncio.sleep(3)

    browse = await open_browser(page=page)

    try:
        iframe=await page.query_selector('iframe')
        content=await iframe.content_frame()

        while await content.is_visible('div.captcha'):
            await asyncio.sleep(5)
            print('Waiting for Captcha to be solved')
        
        await asyncio.sleep(5)
    except:
        pass

    await asyncio.sleep(5)

    email_input = await page.query_selector('#Email')
    email = "matti19913@gmail.com"
    await email_input.fill(email)

    password_input = await page.query_selector('#Password')
    await password_input.fill('')
    password = "Copart2023"
    await password_input.fill(password)

    await page.click('text=Remember Me')
    await page.click('button[type="submit"]')
    await asyncio.sleep(5)
    
    try:
        iframe=await page.query_selector('iframe')
        content=await iframe.content_frame()

        while await content.is_visible('div.captcha'):
            await asyncio.sleep(5)
            print('Waiting for Captcha to be solved')
        
        await asyncio.sleep(5)
    except:
        pass

    await page.hover('text=Vehicles')
    await page.click('text=Cars')

    await asyncio.sleep(3)
    if await page.is_visible("text=Accept All"):
        await page.click("text=Accept All")
    elif await page.is_visible("text=I understand"):
        await page.click("text=I understand")

    client = pymongo.MongoClient(os.getenv("MONGOAUTH"))
    db = client['PortalAuction']
    collection = db['Cars']
    newPage = page #await context.new_page()

    count = 0
    while True:
        logged_out = False
        doc = collection.find_one_and_update({"Info": "None"}, {"$set": {"Info": "processing"}}, sort=[("creation_time", ASCENDING)])
        # doc = collection.find_one_and_update({"Info": "processing"}, {"$set": {"Info": None}}, sort=[("creation_time", ASCENDING)])

        if not doc:
            if collection.count_documents({"Info":"processing"}) == 0:
                break
            else:
                procdocs = collection.find({"Info": "processing"})
                for doc in procdocs:
                    carLink = doc['carLink']
                    collection.update_one({"carLink": carLink}, {"$set": {"Info": "None"}})

        carLink = doc['carLink']
        link = carLink.replace("https://www.iaai.com", "")
        print(link)

        if count % 50 == 0:
            await newPage.close()
            newPage = await context.new_page()
            await asyncio.sleep(5)
            await visit(context,carLink, newPage)
        else:
            await visit(context,carLink, newPage)

        try:
            if await (await newPage.query_selector('h1.heading-3')).inner_text() == "Vehicle details are not found for this stock.":
                MainInfo = "Vehicle details are not found for this stock."
                update_query = {"$set": {"Info": MainInfo}}
                collection.update_one({"carLink": carLink}, update_query)
                continue
        except:
            pass

        MainInfo = {}
        name = await (await newPage.query_selector('h1')).inner_text()
        MainInfo['Name'] = name

        # Getting the image of the car
        image_section = await newPage.query_selector('.vehicle-image__thumb-container#spacedthumbs1strow')

        images = await image_section.query_selector_all('img')
        image_urls = [await image.get_attribute('src') for image in images]
        image_urls = [url.replace("&width=161&height=120","&width=850&height=637") for url in image_urls if 'height' in url]

        image_names=[f'{link.replace("/VehicleDetail/","")}{image_urls.index(i)}.jpg' for i in image_urls]
    
        subprocess.Popen(["python", "downloadNupload.py", link, json.dumps(image_urls)])

            
        MainInfo['Images'] = image_names

        # Getting the car details
        infos_section = [i for i in await newPage.query_selector_all('div.tile.tile--data') if await i.query_selector("ul.data-list.data-list--details") and (await (await i.query_selector("h2.data-title")).inner_text() in ["VEHICLE INFORMATION","VEHICLE DESCRIPTION","SALE INFORMATION"])]
        len(infos_section)

        # Scraping Vehicle info , Vehicle Description and Sale Info
        vehicle_info = {}
        vinfo=await infos_section[0].query_selector_all('li.data-list__item')
        for i in vinfo:
            label=await (await i.query_selector('span.data-list__label')).inner_text()
            value=await (await i.query_selector('span.data-list__value')).inner_text()
            if "№ артикула:" in label:
                label="Stock"
            elif "Nr zapasów:" in label:
                label="Stock"
            elif "Nro. de existencia:" in label:
                label="Stock"
            elif "存货编号:" in label:
                label="Stock"
            elif "Stock #:" in label:
                label="Stock"
                
            if "VIN (Status):" in label:
                label=label.replace(" (Status):","")
                value=value.replace(" (OK)","")
            elif "VIN:" in label:
                label=label.replace(":","")
                value=value.replace(" (OK)","")
            
            if "******" in value and "VIN" in label:
                logged_out=True
                break
            
            
            while '\n' in value or '\t' in value or '  ' in value or " (OK)" in value or " (Unknown)" in value:
                value=value.replace('\n','').replace('\t','').replace('  ','').replace(" (OK)","").replace(" (Unknown)","")
            vehicle_info[label]=value
            
        MainInfo['Vehicle Info']=vehicle_info

        if logged_out:
            collection.update_one({"carLink": carLink}, {"$set": {"Info": "None"}})

        vehicle_description = {}
        vdesc=await infos_section[1].query_selector_all('li.data-list__item')
        for i in vdesc:
            label=await (await i.query_selector('span.data-list__label')).inner_text()
            if '\nMore Info' in label:
                label=label.replace(':\nMore Info',':')
            value=await (await i.query_selector('span.data-list__value')).inner_text()
            while '\n' in value or '\t' in value or '  ' in value or " (OK)" in value or " (Unknown)" in value :
                value=value.replace('\n','').replace('\t','').replace('  ','').replace(" (OK)","").replace(" (Unknown)","")

            if "VIN (Status):" in label:
                label=label.replace(" (Status):","")
                value=value.replace(" (OK)","")
            elif "VIN:" in label:
                label=label.replace(":","")
                value=value.replace(" (OK)","")
            
                if "******" in value and "VIN" in label:
                    logged_out=True
                    break
                    
            vehicle_description[label]=value
                
        if logged_out:
            collection.update_one({"carLink": carLink}, {"$set": {"Info": "None"}})
            break
        
        MainInfo['Vehicle Description']=vehicle_description

        sale_info = {}
        sinfo=await infos_section[2].query_selector_all('li.data-list__item')
        for i in sinfo:
            try:
                label=await (await i.query_selector('span.data-list__label')).inner_text()
                label=label.replace(" Jackson (MS)","")
            except Exception as e:
                continue

            try:
                value=await i.query_selector('span.data-list__value')
                if value is not None:
                    value=await value.inner_text()
                elif value is None:
                    value=await i.query_selector('div')
                    value=await value.inner_text()
            except Exception as e:
                pass
            sale_info[label]=value
        MainInfo['Sale Info']=sale_info
        collection.update_one({"carLink": carLink}, {"$set": {"Info": MainInfo}})

        count += 1

    await playwright.stop()

# Run the main function
asyncio.run(main())
