# 1. Install Python3
# 1b. Make sure Python3 is installed (python --version)
# 2. Add pip3 (or make sure it is installed)
# 3. Install selenium for web driver management
# 4. Verity selenium (google "verify python package")

import subprocess
import json
import sys
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Install chromedrivers with brew
# brew cask install chromedriver

# Commented out for testing <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# Run Lighthouse report against login landing page first before logging in
# Runs URL against Lighthouse in command line, which outputs as a JSON file in memory
# url = 'https://account.develop.bigwhitewall.com/log-in?continue=https%3A%2F%2Fdevelop.bigwhitewall.com%2F'
# data = subprocess.check_output(
#    ["./node_modules/.bin/lighthouse", url, "--output", "json"])

# data = json.loads(data)

# audits = data['audits']

# Writes flagged items as CSV file
# w = csv.writer(sys.stdout)

# for audit_name, audit in audits.items():
#    if audit['score'] != None and audit['score'] <= 0:
#        w.writerow([audit['title'], audit['description']])

# Proceed to logging in with headless browser


def setupHeadlessChrome():
    chrome_options = Options()
    # Uncomment later after debugging <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(
        executable_path="chromedriver", options=chrome_options)

    return browser


def loginToPage(browser):
    print('Load login page')

    browser.get(
        'https://account.develop.bigwhitewall.com/log-in?continue=https%3A%2F%2Fdevelop.bigwhitewall.com%2F')

    # This will await the first load on the login page, based on that 'maincontent' is drawn
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "maincontent"))
    )

    print('Loading completed')
    print(element)

    # Time to collect some user info. "input" can be useful here
    # username = h@neverbland.com
    # password = Password1

    # Here we do find the first input element and inputs some text into it
    usernameElement = browser.find_element_by_name("userNameOrEmail")
    passwordElement = browser.find_element_by_name("password")

    usernameElement.send_keys('h@neverbland.com')
    passwordElement.send_keys('Password1')

    # Accept cookies
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Accept')]")[0].click()

    # Clicks wrong button and takes user to register page <<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Press login button
    browser.find_element_by_class_name("light--MuiButtonBase-root").click()


def awaitFirstDrawOnPage(browser):
    # Await the login to complete so we can start checking the page or navigate around
    # You should be able to do this with WebDriverWait
    print("awaitFirstDrawOnPage")


def processPages(browser, pages):
    # Loop through pages and use checkPageWithLighthouse for each of them
    print("processPages")


def checkPageWithLighthouse(browser):
    # Here we want to take a page, await it to be drawn and then check it with Lighthouse
    print("checkPageWithLighthouse")


def closeBrowser(browser):
    print("checkPageWithLighthouse")


pages = ['https://www.example.com', 'https://www.example.com/hello-world']

browser = setupHeadlessChrome()
loginToPage(browser)
awaitFirstDrawOnPage(browser)
processPages(browser, pages)
