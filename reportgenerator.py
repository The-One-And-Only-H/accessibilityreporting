# 1. Install Python3
# 1b. Make sure Python3 is installed (python --version)
# 2. Add pip3 (or make sure it is installed)
# 3. Install selenium for web driver management
# 4. Verity selenium (google "verify python package")

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


class Page:
    def __init__(self, url, requiresCookies):
        self.url = url
        self.requiresCookies = requiresCookies


class Problem:
    def __init__(self, title, description):
        self.title = title
        self.description = description
        self.count = 1


pages = [
    Page('https://account.develop.bigwhitewall.com/log-in', False),
    Page('https://develop.bigwhitewall.com/', True)]


def main():
    args = parseCommandLine()
    ensureLighthouse()
    browser = setupHeadlessChrome(args)
    loginToPage(browser)
    awaitFirstDrawOnPage(browser)
    cookies = browser.get_cookies()
    closeBrowser(browser)
    results = processPages(args, pages, cookies)
    summary = aggregateResults(results)
    emitResult(summary)

# Optional argument to see script running in the browser


def parseCommandLine():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--visible', action='store_true',
                        help='display browser')
    args = parser.parse_args()
    return args

# Filter through problems flagged by the Lighthouse report and collate dupilcates


def aggregateResults(results):
    problems = {}
    for result in results:
        audits = result['audits']
        for audit_name, audit in audits.items():
            if audit['score'] != None and audit['score'] <= 0:
                if audit_name in problems:
                    problems[audit_name].count += 1
                else:
                    problems[audit_name] = Problem(
                        audit['title'], audit['description'])
    return problems

# Create CSV file ordering collated data by count then alphabetically


def emitResult(summary):
    problems = list(summary.values())
    problems.sort(key=lambda p: (-p.count, p.title.lower()))

    # Writes flagged items as CSV file
    with open('report.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(["Count", "Title", "Description"])
        for p in problems:
            w.writerow([p.count, p.title, p.description])

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

# Detect whether Lighthouse should be run with cookies or not


def processPages(args, pages, cookies):
    results = []
    for page in pages:
        if page.requiresCookies:
            results.append(runLighthouseReport(args, page, cookies))
        else:
            results.append(runLighthouseReport(args, page))
    return results

# Run Lighthouse from the command line


def runLighthouseReport(args, page, cookies=None):
    cmd = ['node', './lighthouse/lighthouse-cli', page.url, '--output', 'json']
    if not args.visible:
        cmd.append('--chrome-flags="--headless"')
    if cookies:
        cookies = [{'name': c['name'], 'value': c['value']} for c in cookies]
        cookies = json.dumps(cookies)
        cmd.extend(['--extra-cookies', cookies])

    out = subprocess.check_output(cmd)
    out = json.loads(out)
    return out


def closeBrowser(browser):
    browser.quit()

# Ensure the below Lighthouse pull request taking cookies is installed


def ensureLighthouse():
    here = os.path.dirname(__file__)
    if here:
        os.chdir(here)
    if os.path.exists('lighthouse'):
        return
    # Branch containing --extra-cookies
    # Until https://github.com/GoogleChrome/lighthouse/pull/9170 merged
    print('installing lighthouse')
    subprocess.check_call(
        ["git", "clone", "https://github.com/RynatSibahatau/lighthouse.git"])
    os.chdir('lighthouse')
    subprocess.check_call(["npm", "install", "yarn"])
    subprocess.check_call(["./node_modules/.bin/yarn"])
    subprocess.check_call(["./node_modules/.bin/yarn", "build-all"])
    os.chdir('..')


if __name__ == '__main__':
    main()
