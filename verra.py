from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time
import datetime
import warnings
import sys
import re
import os
import pyotp
import shutil
import csv
from pathlib import Path

def download_file(site, download_element_xpath, new_filename, search=None):
    driver.get(site)
    if search is not None:
        original_window = driver.current_window_handle
        driver.find_element(By.XPATH, search["search_xpath"]).click()
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        select = Select(driver.find_element("id", f"Relation{search['search_field_nr']}"))
        select.select_by_value(search["search_operator"])
        driver.find_element("id", f"Field{search['search_field_nr']}").send_keys(search['search_value'])
        driver.find_element(By.NAME, "Search").click()
        driver.switch_to.window(original_window)
    if search is not None:
        index = re.match('.+([0-9])[^0-9]*$', download_element_xpath).start(1)
        new_download_element_xpath = list(download_element_xpath)
        new_download_element_xpath[index] = str(int(new_download_element_xpath[index])+1)
        new_download_element_xpath = ''.join(new_download_element_xpath)
        driver.find_element(By.XPATH, new_download_element_xpath).click()
    else:
        driver.find_element(By.XPATH, download_element_xpath).click()
    time.sleep(5)
    for i in range(1,16):
        chrome_temp_file = sorted(Path(download_folder).glob('*.crdownload'))
        if len(chrome_temp_file) == 0:
            if os.path.isfile(os.path.join(download_folder, "temp.csv")):
                break
            elif i == 15:
                print("error: finde temp.csv nicht")
        elif i == 15:
            print("error: download dauert zu lange")
        time.sleep(1)
    # filename = max([download_folder + "/" + f for f in os.listdir(download_folder)],key=os.path.getctime)
    filename = os.path.join(download_folder, "temp.csv")
    new_file = os.path.join(download_folder, f"{new_filename}{datetime.date.today().isoformat()}.csv")
    shutil.move(filename, new_file)
    return new_file

warnings.filterwarnings("ignore")
download_folder = f"{os.getcwd()}/files"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)
options = Options()
# options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
options.add_argument(f"--user-agent={user_agent}")
prefs = {'download.default_directory' : download_folder}
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(15)

driver.get("https://registry.verra.org/mymodule/mypage.asp?p=login")

driver.find_element("id", "myuserid").send_keys(os.getenv("verra_username"))
driver.find_element("id", "mypassword").send_keys(os.getenv("verra_pw"))
driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div/div/div/div[2]/form/button").click()

totp = pyotp.parse_uri(os.getenv("verra_totp_uri"))

driver.find_element("id", "mfacode").send_keys(totp.now())
driver.find_element(By.NAME, "Continue").click()

primary_accounts_file = download_file(
    "https://registry.verra.org/myModule/rpt/MyAHrpt.asp?r=601&TabName=Primary%20Account&ID=0",
    "/html/body/div[2]/div/center/div/div/form/div/div/div/div/div/div[1]/div[2]/a[2]",
    "primary_accounts_"
)

retirement_sub_accounts_file = download_file(
    "https://registry.verra.org/myModule/rpt/MyAHrpt.asp?r=601&TabName=Retirement+Sub%2DAccounts",
    "/html/body/div[2]/div/center/div/div[2]/div/div/div/div[1]/div[2]/a[2]",
    "retirement_sub_accounts_"
)

inter_account_transfer_file = download_file(
    "https://registry.verra.org/myModule/rpt/MyAHrpt.asp?r=404&TabName=Inter-Account%20Transfer",
    "/html/body/div[2]/div/center/div/div/div/div/div/div[1]/div[2]/a[2]",
    "inter_account_transfer_",
    {
        "search_xpath": "/html/body/div[2]/div/center/div/div/div/div/div/div[1]/div[2]/a[1]",
        "search_field_nr": "11",
        "search_operator": "=",
        "search_value": "Confirm"
    }
)

all_projects_file = download_file(
    "https://registry.verra.org/myModule/rpt/myAHrpt.asp?r=208&TabName=All",
    "/html/body/div[2]/div/center/div/div/div/div/div/div[1]/div[2]/a[2]",
    "all_projects_"
)

project_ids = []
with open(all_projects_file, mode='r') as file:
    csv_reader = csv.reader(file)
    next(csv_reader, None)
    for row in csv_reader: 
        project_ids.append(row[0])

os.remove(all_projects_file)

count = 0
single_project_files = []
for project_id in project_ids:
    if count == 5:
        break
    count += 1
    single_project_files.append(
        download_file(
            f"https://registry.verra.org/mymodule/rpt/myAHrpt.asp?r=617&id1={project_id}",
            "/html/body/div[2]/div[2]/div/div/div/div[1]/div[2]/a[2]",
            f"project_{project_id}_"
        )
    )

time.sleep(15)