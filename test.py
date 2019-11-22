# 1. Install Python3
# 1b. Make sure Python3 is installed (python --version)
# 2. Add pip3 (or make sure it is installed)
# 3. Install selenium for web driver management
# 4. Verity selenium (google "verify python package")

import json
import subprocess
import sys
import csv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Install chromedrivers with brew
# brew cask install chromedriver


class ClassPage:
    def __init__(self, _url, _requiresCookies):
        self.url = _url
        self.requiresCookies = _requiresCookies


pages = [ClassPage('https://account.develop.bigwhitewall.com/log-in',
                   True), ClassPage('https://develop.bigwhitewall.com/', False)]


def main():
    browser = setupHeadlessChrome()
    loginToPage(browser)
    awaitFirstDrawOnPage(browser)
    cookies = browser.get_cookies()
    closeBrowser(browser)
    results = processPages(pages, cookies)
    # import pdb
    # pdb.set_trace()


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
        'https://account.develop.bigwhitewall.com/log-in')

    # This will await the first load on the login page, based on that 'maincontent' is drawn
    element = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "maincontent"))
    )

    print('Loading completed')
    print(element)

    # Time to collect some user info. "input" can be useful here
    # username = h@neverbland.com
    # password = Password1

    # Here we do find the first input element and inputs some text into it
    usernameElement = browser.find_element_by_name("userNameOrEmail")
    passwordElement = browser.find_element_by_name("password")

    usernameElement.send_keys('h@neverbland.com')
    passwordElement.send_keys('Password1')

    # Accept the cookies
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Accept')]")[0].click()
    element = WebDriverWait(browser, 10).until_not(
        EC.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Accept')]"))
    )

    # Press the login button
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Log in')]")[0].click()
    element = WebDriverWait(browser, 10).until_not(
        EC.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Log in')]"))
    )


def awaitFirstDrawOnPage(browser):
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Hi')]"))
    )


def processPages(pages, cookies):
    results = []
    for page in pages:
        if page.requiresCookies:
            results.append(checkPageWithLighthouse(page, cookies))
        else:
            results.append(checkPageWithLighthouse(page))


def checkPageWithLighthouse(page, cookies=None):
    cmd = ['node', './lighthouse/lighthouse-cli', page.url, '--output', 'json']
    if cookies:
        cookies = [{'name': c['name'], 'value': c['value']} for c in cookies]
        cookies = json.dumps(cookies)
        cmd.extend(['--extra-cookies', cookies])

        # print("cookies:", cookies)
        # print("cmd:", cmd)

    out = subprocess.check_output(cmd)
    out = json.loads(out)

    audits = out['audits']

    # print("audits:", audits)

    # Writes flagged items as CSV file
    w = csv.writer(open("report.csv", "w"))

    for audit_name, audit in audits.items():
        # print("auditScore:", audit['score'])
        if audit['score'] != None and audit['score'] <= 0:
            w.writerow([audit['title'], audit['description']])


def closeBrowser(browser):
    browser.quit()


if __name__ == '__main__':
    main()

    #w = csv.writer(open("report.csv", "w"))

    #w.writerow("Hello world")
