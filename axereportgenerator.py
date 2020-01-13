import logging
import yaml
import csv

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as SeleniumExpectedConditions
from selenium.webdriver.common.by import By
from axe_selenium_python import Axe
from argparse import ArgumentParser

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s')


class Problem:
    def __init__(self, impact, help, description, helpUrl):
        self.impact = impact
        self.help = help
        self.description = description
        self.helpUrl = helpUrl
        self.count = 0

    def incrementCount(self, value):
        self.count += value


class ProblemAggregator:
    def __init__(self):
        self.problems = {}

    def addResult(self, result):
        audits = result['violations']
        for audit in audits:
            if audit['impact'] != None:
                if audit['id'] not in self.problems:
                    self.problems[audit['id']] = Problem(
                        audit['impact'], audit['help'], audit['description'], audit['helpUrl'])
                problem = self.problems[audit['id']]
                problem.incrementCount(len(audit['nodes']))

    def getSummary(self):
        return self.problems


def main():
    args = parseCommandLine()
    pages = loadInputFile(args)
    results = processPages(args, pages)
    summary = aggregateResults(results)
    emitResults(summary)

# Optional argument to see script running in the browser


def parseCommandLine():
    parser = ArgumentParser()
    parser.add_argument('--visible', action='store_true',
                        help='display browser')
    parser.add_argument(
        'input', help='runs script against chosen list of URLs')
    args = parser.parse_args()
    return args

# Loads data from yaml file passed through the command line


def loadInputFile(args):
    with open(args.input) as file:
        data = yaml.load(file.read(), Loader=yaml.SafeLoader)
    return data['pages']


# Filter through problems flagged by the Axe report and collate duplicates


def aggregateResults(results):
    ag = ProblemAggregator()
    for result in results:
        ag.addResult(result)
    return ag.getSummary()

# Create CSV file ordering collated data by count then alphabetically


def emitResults(summary):
    problems = list(summary.values())

    # Sort problems in order of highest occurrence to lowest
    def getCount(p):
        return p.count

    problems.sort(key=getCount, reverse=True)

    # Writes flagged items as CSV file
    with open('report.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(["Count", "Priority", "Title", "Description", "More info"])
        for p in problems:
            w.writerow([p.count, p.impact, p.help, p.description, p.helpUrl])

# Hide Selenium running in browser when running script


def setupHeadlessChrome(args):
    chrome_options = ChromeOptions()
    if not args.visible:
        chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(
        executable_path="chromedriver", options=chrome_options)

    return browser


def loginToPage(browser):
    logger.info('Loads login page')

    browser.get(
        'https://account.develop.bigwhitewall.com/log-in')

    # This will await the first load on the login page, based on that 'maincontent' is drawn
    WebDriverWait(browser, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.ID, "maincontent"))
    )

    logger.info('Login page loading completed')

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
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Accept')]"))
    )

    # Press the login button
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Log in')]")[0].click()
    WebDriverWait(browser, 10).until_not(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Log in')]"))
    )

# Detect element on landing page after log in


def awaitFirstDrawOnPage(browser):
    WebDriverWait(browser, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
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
    logger.info("Running Axe against %s", page['url'])
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
