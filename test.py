from fastapi import FastAPI
from fastapi.responses import FileResponse,JSONResponse
import pandas as pd
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
import pymongo
import requests

app = FastAPI()

client = pymongo.MongoClient("mongodb+srv://muskanearnestrio:ZNxqy0n23QASuwyB@cluster0.muwhsjj.mongodb.net/")
db = client["scraping"]
collection = db["testingthroughapi"]

class XPathInput(BaseModel):
    main_url: str
    xpaths: list

def is_url_restricted(url):
    try:
        response = requests.get(url)
        if response.status_code == 403:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def extract_data(main_url, xpaths):
    if is_url_restricted(main_url):
        return JSONResponse(content={"error": "The website is restricted for scraping", "status_code": 403})

    driver_path = 'D:/bscscan/chromedriver-win64/chromedriver.exe'
    s = Service(driver_path)
    driver = webdriver.Chrome(service=s)

    try:
        driver.get(main_url)
        driver.implicitly_wait(20)

        for xpath in xpaths:
            elements = driver.find_elements(By.XPATH, xpath)

            for element in elements:
                data = element.text
                if not data:
                    return JSONResponse(content={"error": "Data cannot be extracted from the specified XPath"}, status_code=400)

                data_dict = {"data": data}
                collection.insert_one(data_dict)
                print(f"Data {data} inserted into MongoDB")
        return {"message": "Data scraping completed"}

    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(content={"error":f"An error occurred: {e}"},status_code=500)
    finally:
        driver.quit()

@app.post("/scrape")
async def scrape_data(xpaths: XPathInput):
    main_url = xpaths.main_url
    xpaths_list = xpaths.xpaths
    result = extract_data(main_url, xpaths_list)
    if "error" in result:
        return result, result["status_code"]
    return {"message": "Data scraping completed"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
