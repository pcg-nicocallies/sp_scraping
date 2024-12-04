from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import datetime
import warnings
import os
import pyotp
import csv
from google.cloud import storage
from cloud_logging import cloud_logging
from download_file import download_file

def main():
    warnings.filterwarnings("ignore")
    download_folder = f"{os.getcwd()}/files"
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    today = datetime.date.today().isoformat()
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
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
        driver,
        download_folder,
        today,
        "https://registry.verra.org/myModule/rpt/MyAHrpt.asp?r=601&TabName=Primary%20Account&ID=0",
        "/html/body/div[2]/div/center/div/div/form/div/div/div/div/div/div[1]/div[2]/a[2]",
        "primary_accounts"
    )

    retirement_sub_accounts_file = download_file(
        driver,
        download_folder,
        today,
        "https://registry.verra.org/myModule/rpt/MyAHrpt.asp?r=601&TabName=Retirement+Sub%2DAccounts",
        "/html/body/div[2]/div/center/div/div[2]/div/div/div/div[1]/div[2]/a[2]",
        "retirement_sub_accounts"
    )

    inter_account_transfer_file = download_file(
        driver,
        download_folder,
        today,
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
        driver,
        download_folder,
        today,
        "https://registry.verra.org/myModule/rpt/myAHrpt.asp?r=208&TabName=All",
        "/html/body/div[2]/div/center/div/div/div/div/div/div[1]/div[2]/a[2]",
        "all_projects"
    )

    project_ids = []
    with open(all_projects_file, mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader, None)
        for row in csv_reader: 
            project_ids.append(row[0])
    
    project_ids = list(dict.fromkeys(project_ids))

    os.remove(all_projects_file)

    single_project_files = []
    for project_id in project_ids:
        single_project_files.append(
            download_file(
                driver,
                download_folder,
                today,
                f"https://registry.verra.org/mymodule/rpt/myAHrpt.asp?r=617&id1={project_id}",
                "/html/body/div[2]/div[2]/div/div/div/div[1]/div[2]/a[2]",
                f"project_{project_id}"
            )
        )

    time.sleep(15)
    driver.quit()

    all_files = [primary_accounts_file, retirement_sub_accounts_file, inter_account_transfer_file] + single_project_files
    client = storage.Client(project='cw-nico-sandbox')
    bucket = client.get_bucket('pcg_sp_verra_test')
    for file in all_files:
        filename = file.split('/')[-1]
        blob = bucket.blob(f'{today}/{filename}')
        blob.upload_from_filename(f'{file}')

if __name__ == '__main__':
    main()