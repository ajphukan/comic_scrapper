from selenium import webdriver
from selenium.webdriver.common.utils import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import img2pdf

from time import sleep
import os
import requests
import random
import re


regex_for_id = r"(id=\d+)"
BASE_DIR =  os.path.join(os.path.expanduser('~'),'comic')
def is_comic_base_folder():
    return os.path.isdir(BASE_DIR)

def is_comic_folder(comic_name):
    comic_name_dir = os.path.join(BASE_DIR, comic_name)
    return os.path.isdir(comic_name_dir)

def make_folder(comic_name=None):
    if comic_name is not None:
        comic_name_dir = os.path.join(BASE_DIR, comic_name)
    else:
        comic_name_dir = BASE_DIR
    if not os.path.exists(comic_name_dir):
        os.mkdir(comic_name_dir)
    return comic_name_dir

def make_comic_folder():
    make_folder()

def get_comic_name(driver):
    comic_name = driver.find_element_by_css_selector("#navsubbar > p >a").text
    comic_name += " " + driver.find_element_by_css_selector(".selectEpisode > option[selected]").text.strip()
    return comic_name

def get_list_of_pages(driver):    
    comic_pg_img_url_list = driver.execute_script("return lstImages;") # []
    return comic_pg_img_url_list


def download_img(img_info):
    url, file_name = img_info
    with requests.get(url, stream=True) as r:
        image = r.raw.read()
        open(file_name, "wb").write(image)
        print(f"File Downloaded: {file_name}")


def download_img_from_json(comic_json):
    download_list =[]
    for comic_name in comic_json.keys():
        comic_folder = make_folder(comic_name)
        img_urls = comic_json[comic_name]["page_list"]
        for id, url in enumerate(img_urls):
            file_name = os.path.join(comic_folder, str(id+1)+".jpg")
            if not os.path.isfile(file_name):
                download_list.append((url, file_name))
            else:
                print(f"File Present: {file_name}")

    for ele in download_list:
        download_img(ele)
    
def create_pdf_from_json(comic_json):
    for comic_name_folder in comic_json.keys():
        comic_folder = os.path.join(BASE_DIR, comic_name_folder)
        comic_name = comic_json[comic_name_folder]["comic_name"]
        comic_pdf = os.path.join(comic_folder,comic_name + ".pdf")
        if not os.path.isfile(comic_pdf):
            no_of_pages = comic_json[comic_name_folder]["page_count"]
            images = [ os.path.join(comic_folder, str(id+1)+".jpg") for id in range( no_of_pages)]
            with open(comic_pdf,"wb") as f:
                f.write(img2pdf.convert(images))


def get_comic_name_and_page_ls(driver, url):
    matches = re.findall(regex_for_id, url, re.MULTILINE)
    url = url.split('?')[0] + '?' + "&".join([matches[0],'quality=hq','readtype=1'])
    print(f"Opening url : {url}")
    driver.get(url)
    try:
        comic_name = get_comic_name(driver)
    except Exception as e:
        print("Exception Occur: ", e)
        ch = input("Please Solve the Recaptcha then Press Enter: ")
        comic_name = get_comic_name(driver)

    page_list = get_list_of_pages(driver)
    return comic_name , page_list

def download_comic(driver, urls , comic_coll = None):
    comic_json = {}
    if comic_coll:
        for url in urls:
            try:
                comic_name, page_list = get_comic_name_and_page_ls(driver, url)
            except Exception as e:
                print("Exception Occur: ", e)
                break
            sleep(random.randint(5, 10))  # Added Delay to prevent load on web server
            comic_name_folder = os.path.join(comic_coll,comic_name)
            comic_json[comic_name_folder] = {
            "comic_name": comic_name,
            "page_list": page_list,
            "page_count":len(page_list)
            }
            print(comic_json[comic_name_folder])
    else:
        comic_name, page_list = get_comic_name_and_page_ls(driver, urls)
        comic_json[comic_name] = {
            "comic_name": comic_name,
            "page_list": page_list,
            "page_count": len(page_list)
        }
    driver.close()
    download_img_from_json(comic_json)
    create_pdf_from_json(comic_json)
    print(f"Check Comic directory for {comic_name} surprise")
    

def download_comic_coll(driver, url):
    driver.get(url)
    sleep(15)
    # ch = input("Enter any character to continue")
    try:
        comic_coll = driver.find_element_by_css_selector(".barContent > div > a.bigChar").text
        print(f"Downloading your comic Collection {comic_coll}")
    except NoSuchElementException as e:
        print("You have a provide link for downloading single comic issue")
        download_comic(driver, url)
        return

    make_folder(comic_coll)
    comic_urls = list(map(lambda ele: ele.get_attribute("href"),driver.find_elements_by_css_selector(".listing > tbody > tr > td > a")))
    comic_urls.reverse() # Comics were downloading in reverse order 
    download_comic(driver, comic_urls, comic_coll)

if __name__ == "__main__":
    url = "https://readcomiconline.to/Comic/Injustice-Ground-Zero"
    if not is_comic_base_folder(): # only in first run
        make_comic_folder()
    

    chrome_options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.headless = True
    driver = webdriver.Chrome()
    download_comic_coll(driver, url)
