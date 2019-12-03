# 1. Install Python3
# 1b. Make sure Python3 is installed (python --version)
# 2. Add pip3 (or make sure it is installed)
# 3. Install selenium for web driver management
# 4. Verity selenium (google "verify python package")

# pip install pyyaml

import yaml
import json
import subprocess
import csv
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Install chromedrivers with brew
# brew cask install chromedriver

from axe_selenium_python import Axe


class Problem:
    def __init__(self, impact, help, description, helpUrl):
        self.impact = impact
        self.help = help
        self.description = description
        self.helpUrl = helpUrl
        self.count = 0


def main():
    args = parseCommandLine()
    pages = loadInputFile(args)
    results = processPages(args, pages)
    summary = aggregateResults(results)
    emitResult(summary)

# Optional argument to see script running in the browser


def parseCommandLine():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--visible', action='store_true',
                        help='display browser')
    # Run script with urls.yaml or any .yaml file containing URLs - add this to README <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    parser.add_argument(
        'input', help='runs script against chosen list of URLs')
    args = parser.parse_args()
    return args

# Loads data from yaml file passed through the command line


def loadInputFile(args):
    with open(args.input) as f:
        data = yaml.load(f.read(), Loader=yaml.SafeLoader)
    return data['pages']

# Filter through problems flagged by the Axe report and collate dupilcates
# Count number of items in details of error from JSON blob


def aggregateResults(results):
    problems = {}
    for result in results:
        audits = result['violations']
        for audit in audits:
            if audit['impact'] != None:
                if audit['id'] not in problems:
                    problems[audit['id']] = Problem(
                        audit['impact'], audit['help'], audit['description'], audit['helpUrl'])
                problem = problems[audit['id']]
                if 'details' in audit and 'items' in audit['details'] and audit['details']['items']:
                    problem.count += len(audit['details']['items'])
                else:
                    problem.count += 1
    return problems

# Create CSV file ordering collated data by count then alphabetically


def emitResult(summary):
    problems = list(summary.values())
    problems.sort(key=lambda p: (-p.count))

    # Writes flagged items as CSV file
    with open('report.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(["Count", "Priority", "Title", "Description", "More info"])
        for p in problems:
            w.writerow([p.count, p.impact, p.help, p.description, p.helpUrl])

# Hide Selenium running in browser when running script


def setupHeadlessChrome(args):
    chrome_options = Options()
    if not args.visible:
        chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(
        executable_path="chromedriver", options=chrome_options)

    return browser


def loginToPage(browser):
    print('Load login page')

    browser.get(
        'https://account.develop.bigwhitewall.com/log-in')

    # This will await the first load on the login page, based on that 'maincontent' is drawn
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "maincontent"))
    )

    print('Loading completed')

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
    WebDriverWait(browser, 10).until_not(
        EC.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Accept')]"))
    )

    # Press the login button
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Log in')]")[0].click()
    WebDriverWait(browser, 10).until_not(
        EC.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Log in')]"))
    )

# Detect element on landing page after log in


def awaitFirstDrawOnPage(browser):
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Hi')]"))
    )


# Detect whether Axe should be run with log in details or not


def processPages(args, pages):
    results = []
    for page in pages:
        browser = setupHeadlessChrome(args)
        if page.get('require_login'):
            loginToPage(browser)
            awaitFirstDrawOnPage(browser)
        results.append(runAxeReport(browser, args, page))
        closeBrowser(browser)
    return results

# Run Axe from the command line


def runAxeReport(browser, args, page):
    pageUrl = page['url']
    browser.get(pageUrl)
    axe = Axe(browser)
    # Inject axe-core javascript into page
    axe.inject()
    # Run axe accessibility checks
    results = axe.run()
    return results


def closeBrowser(browser):
    browser.quit()


if __name__ == '__main__':
    main()
