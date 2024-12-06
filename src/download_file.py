from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import re
import os
import shutil
from pathlib import Path

def download_file(driver, download_folder, today, site, download_element_xpath, new_filename, search=None):
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
    new_file = os.path.join(download_folder, f"{new_filename}_{today}.csv")
    shutil.move(filename, new_file)
    return new_file