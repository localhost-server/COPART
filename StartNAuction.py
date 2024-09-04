import argparse
from playwright.async_api import async_playwright
# from undetected_playwright.async_api import async_playwright
import subprocess 
import asyncio
import pymongo
from pymongo import UpdateOne
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz
import re

load_dotenv()

# Create a new client
client = pymongo.MongoClient(os.getenv("MONGO_URI"))

# Get a reference to the database
db = client['Copart']

# Get a reference to the collection
collection = db['CarsPrice']
link_collection = db['AuctionLinks']

# Setting CDT timezone
cdt=pytz.timezone('America/Chicago')

async def open_browser(page, weblink):
    await page.emulate_media(color_scheme='dark')
    await page.goto(weblink, wait_until='load')
    return page

async def scrape_auction_data(collection, link_collection):
    start_time = datetime.now()
    playwright = await async_playwright().start()
    args = ["--disable-blink-features=AutomationControlled"]
    browser = await playwright.firefox.launch(headless=True)

    context = await browser.new_context()
    page = await context.new_page()
    browse = await open_browser(page=page, weblink="https://www.copart.com/login/") 
    await asyncio.sleep(20)

    try:
        email_input = await page.query_selector('#username')
        email = "matti19913@gmail.com"
        await email_input.fill(email)
        password_input = await page.query_selector('#password')
        password = "Copart2023!"
        await password_input.fill(password)
        await page.click('text=Remember?')
        await page.click('text=Sign Into Your Account')
        await asyncio.sleep(20)
    except:
        print("Bot detected")
        await page.close()
        await browser.close()
        return
        # link_collection.update_one({'link': auction_link}, {'$set': {'Info': 'None'}})

    count=0
    data={}

    # cursor = link_collection.find_one_and_update({"Info": "None"}, {"$set": {"Info": "Processing"}})
    # auction_link = cursor['link']
    # print(auction_link)
    # await page.goto(auction_link, wait_until='load')
    await page.goto("https://www.copart.com/auctionDashboard")
    await asyncio.sleep(30)

    iframe_element=await page.query_selector('div.auction5iframe')
    iframe=await iframe_element.query_selector("iframe")
    content = await iframe.content_frame()

    await asyncio.sleep(5)
    print("Opening links")
    count=10 if link_collection.count_documents({"Info": "None"})>9 else link_collection.count_documents({"Info": "None"})
    # Setting the limit of auctions to be added 
    while len(await content.query_selector_all('gridster-item.ng-star-inserted'))<count:
        add_auction=await content.wait_for_selector('span.nav-option-on.addauctionbtn')
        await asyncio.sleep(3)
        await add_auction.click()
        all_auctions=await content.query_selector_all('text.ng-star-inserted')
    
    baseauction_url="https://www.copart.com/auctionDashboard?auctionDetails="
    await asyncio.sleep(5)
    # checking auction sections
    all_auctions=await content.query_selector_all('gridster-item.ng-star-inserted')

    # For managing the auction
    collected_auctions=set()
    aucCount=0
    for check in all_auctions:
        aucCount+=1
        join_button=await check.query_selector_all('tr.liveAuction.ng-star-inserted')
        if join_button:
            for i in join_button:
                locale=await i.query_selector('div.yardName-MACRO')
                auction_locale=await locale.get_attribute('title')
                auction_locale=auction_locale.split(" - ")[-1]
                auction_locale = re.sub(r'(\d)([A-Za-z])$', r'\1-\2', auction_locale)
                # clicking on the join button
                complete_link = baseauction_url+auction_locale
                if not link_collection.find_one({"link": complete_link,"Info": "None"}):
                    pass
                else:
                    link_collection.find_one_and_update({"link": complete_link}, {"$set": {"Info": "Processing"}})
                    collected_auctions.add(baseauction_url+auction_locale)
                    print(auction_locale)
                    await i.click()
                    break
        if aucCount>5:
            all_auctions=await content.query_selector_all('gridster-item.ng-star-inserted')
        await asyncio.sleep(2)
    
    iframe_element=await page.query_selector('div.auction5iframe')
    iframe=await iframe_element.query_selector("iframe")
    content = await iframe.content_frame()
    all_auctions=await content.query_selector_all('gridster-item.ng-star-inserted')
    await asyncio.sleep(20)
    while True:
        end_time = datetime.now()
        initial_count=len(data)
        
        count+=1

        for check in all_auctions:
            # For extracting data from auction
            car_link=await check.query_selector('a.titlelbl.ellipsis')
            try:
                link=await car_link.get_attribute("href")
                # print(link)
                if "https" in link:
                    car_price=await check.query_selector('text.ng-star-inserted')
                    checked=await car_price.text_content()
                    price=checked.replace("\n","").replace(" ","")
                    if "$" in price:
                        data[link]=price

                # Convert price to a number, assuming it's a string like "$1000"
                new_price = float(price.replace("$", "").replace(",","")) if price and "$" in price else 0
                if str(link) in data:
                    # Get the existing price and convert it to a number
                    existing_price = float(data[str(link)].replace("$", "").replace(",","")) if data[str(link)] else 0

                    # Update the price only if the new price is greater than the existing one
                    if new_price > existing_price:
                        data[str(link)] = price

                        # print({link: price}, end=' , ')
                else:
                    # If the identity link is not in data, add it
                    data[str(link)] = price
                # print({link: price}, end=' , ')
            except:
                pass
        final_count=len(data)
        if count>20:
            # print(data)
            iframe_element=await page.query_selector('div.auction5iframe')
            iframe=await iframe_element.query_selector("iframe")
            content = await iframe.content_frame()
            all_auctions=await content.query_selector_all('gridster-item.ng-star-inserted')
            count=0

            all_ended_auctions=[i for i in all_auctions if await i.query_selector('div.sale-end.text-center')]
            if (len(all_auctions)==len(all_ended_auctions)) or ((end_time - start_time).total_seconds()/60>600) or ((final_count-initial_count)==0 and (end_time - start_time).total_seconds()/60>120):
                print("No of auctions ended: ",len(all_ended_auctions))

                await asyncio.sleep(2)
                await page.close()
                await browser.close()

                data_list = [{"carLink": k, "price": int(v.replace("$",'').replace(",",'')) , "date": datetime.now(cdt).date().strftime("%d-%m-%Y").replace('-','.')} for k, v in data.items() if "https://www.copart.com/" in k and v != ""]
                carLink_list = [i['carLink'] for i in data_list]

                subprocess.Popen(["python3", "check_link.py", ' '.join(carLink_list)])
                print(f"Data captured of {len(data_list)} cars")
                print(data_list)

                from pymongo import UpdateOne
                # Prepare bulk write operations
                operations = []
                for carsdata in data_list:
                    price_obj = {"date": carsdata["date"], "price": carsdata["price"]}
                    operations.append(
                        UpdateOne(
                            {"carLink": carsdata["carLink"]},
                            {"$push": {"prices": price_obj}, "$setOnInsert": {"carLink": carsdata["carLink"]}},
                            upsert=True
                        )
                    )

                # Execute bulk write operations
                collection.bulk_write(operations)

                for auction in collected_auctions:
                    link_collection.find_one_and_update({"link": auction}, {"$set": {"Info": "done"}})
                break

    # while True:
    #     end_time = datetime.now()
    #     # checking if it went 5 hours on auction and close it
    #     if (end_time - start_time).total_seconds()/60>300:
    #         print(f'Auction Closed {auction_link}')
    #         await page.close()
    #         await browser.close()

    #         if not data:
    #             return

    #         data_list = [{"carLink": k, "price": v , "date": datetime.now(cdt).date().strftime("%d-%m-%Y").replace('-','.')} for k, v in data.items() if k != 'None' and v != ""]
    #         carLink_list = [i['carLink'] for i in data_list]

    #         subprocess.Popen(["python3", "check_link.py", ' '.join(carLink_list)])
    #         print(f"Data captured of {len(data_list)} cars")
    #         print(data_list)

    #         # Prepare bulk write operations
    #         operations = []
    #         for data in data_list:
    #             price_obj = {"date": data["date"], "price": data["price"]}
    #             operations.append(
    #                 UpdateOne(
    #                     {"carLink": data["carLink"]},
    #                     {"$push": {"prices": price_obj}, "$setOnInsert": {"carLink": data["carLink"]}},
    #                     upsert=True
    #                 )
    #             )

    #         # Execute bulk write operations
    #         collection.bulk_write(operations)
    #         # collection.insert_many(data_list)
            
            
    #         link_collection.update_one({'link': auction_link}, {'$set': {'Info': 'done'}})

    #         return
            
    #     await page.wait_for_selector('div.AuctionContainer.event__item')
    #     multiple_auc_in_single_page = await page.query_selector_all('div.AuctionContainer.event__item')
    #     # auctioning_completed = await page.query_selector_all("div.event-empty__content")
    #     auctioning_completed = await page.query_selector_all('h2.event-empty__title[data-translate="AuctionCompleted"]')
    #     # print(f'Number of auctions in the page: {len(multiple_auc_in_single_page)}')
    #     # print(f'Number of auctions completed: {len(auctioning_completed)}')
    #     if (len(auctioning_completed)>0) and (len(auctioning_completed) == len(multiple_auc_in_single_page)) and ((end_time - start_time).total_seconds()/60 > 30):

    #         print(f'Auction Closed {auction_link}')
    #         await page.close()
    #         await browser.close()

    #         if not data:
    #             return

    #         data_list = [{"carLink": k, "price": v , "date": datetime.now(cdt).date().strftime("%d-%m-%Y").replace('-','.')} for k, v in data.items() if k != 'None' and v != ""]
    #         carLink_list = [i['carLink'] for i in data_list]

    #         subprocess.Popen(["python3", "check_link.py", ' '.join(carLink_list)])
    #         print(f"Data captured of {len(data_list)} cars")
    #         print(data_list)

    #         # Prepare bulk write operations
    #         operations = []
    #         for data in data_list:
    #             price_obj = {"date": data["date"], "price": data["price"]}
    #             operations.append(
    #                 UpdateOne(
    #                     {"carLink": data["carLink"]},
    #                     {"$push": {"prices": price_obj}, "$setOnInsert": {"carLink": data["carLink"]}},
    #                     upsert=True
    #                 )
    #             )

    #         # Execute bulk write operations
    #         collection.bulk_write(operations)
    #         # collection.insert_many(data_list)
            
            
    #         link_collection.update_one({'link': auction_link}, {'$set': {'Info': 'done'}})

    #         return
    #     else:
    #         if multiple_auc_in_single_page:
    #             for auc in multiple_auc_in_single_page:
    #                 content = await auc.query_selector('span.stock-number')
    #                 if content is None:
    #                     continue
    #                 internal_link = await content.query_selector('a')
    #                 if internal_link is None:
    #                     continue
    #                 else:
    #                     identity = await internal_link.get_attribute('href')

    #                 try:
    #                     price=None
    #                     await auc.wait_for_selector('div.js-BidActions')
    #                     content = await auc.query_selector('div.js-BidActions')
    #                     high_bid_element = await content.query_selector("span.high-bid__amount")
    #                     if high_bid_element is not None:
    #                         price = await high_bid_element.inner_text()
    #                     else:
    #                         bid_now_element = await content.query_selector("span.bid-now__amount")
    #                         if bid_now_element is not None:
    #                             price = await bid_now_element.inner_text()
    #                             del bid_now_element
    #                         else:
    #                             price = ""
    #                 except:
    #                     if not price:
    #                         price = ""
    #                     continue

    #                 # Convert price to a number, assuming it's a string like "$1000"
    #                 new_price = float(price.replace("$", "").replace(",","")) if price else 0

    #                 # Check if the identity link is in data
    #                 if str(identity) in data:
    #                     # Get the existing price and convert it to a number
    #                     existing_price = float(data[str(identity)].replace("$", "").replace(",","")) if data[str(identity)] else 0
                    
    #                     # Update the price only if the new price is greater than the existing one
    #                     if new_price > existing_price:
    #                         data[str(identity)] = price
    #                         print({identity: price}, end=' , ')
    #                 else:
    #                     # If the identity link is not in data, add it
    #                     data[str(identity)] = price
    #                     print({identity: price}, end=' , ')
                    
    #                 del content, internal_link, identity, price, high_bid_element, auc
    #                 await asyncio.sleep(2.3)
    

# Usage
asyncio.run(scrape_auction_data(collection, link_collection))
