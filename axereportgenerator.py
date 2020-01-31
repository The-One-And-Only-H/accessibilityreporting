import logging

import yaml

import openpyxl
from openpyxl.styles import Font

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as SeleniumExpectedConditions
from selenium.webdriver.common.by import By

from axe_selenium_python import Axe

from argparse import ArgumentParser

# Log more information messages to the shell

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s')


class ProblemAggregator:
    def __init__(self):
        self.problems = {}

    def addResult(self, result):
        audits = result['violations']
        for audit in audits:
            if audit['impact'] is None:
                continue
            if audit['id'] not in self.problems:
                self.problems[audit['id']] = Problem(
                    audit['impact'], audit['help'], audit['description'], audit['helpUrl'])
            problem = self.problems[audit['id']]
            problem.incrementCount(len(audit['nodes']))

    def getSummary(self):
        return self.problems


class Problem:
    def __init__(self, impact, help, description, helpUrl):
        self.impact = impact
        self.help = help
        self.description = description
        self.helpUrl = helpUrl
        self.count = 0

    def incrementCount(self, value):
        self.count += value


def main():
    args = parseCommandLine()
    data = loadInputFile(args)
    results = processPages(args, data)
    summary = aggregateResults(results)
    emitResults(summary)

# Optional argument to see script running in the brosheeter


def parseCommandLine():
    parser = ArgumentParser()
    parser.add_argument('--visible', action='store_true',
                        help='display brosheeter')
    parser.add_argument(
        'input', help='runs script against chosen list of URLs')
    args = parser.parse_args()
    return args

# Loads data from yaml file passed through the command line


def loadInputFile(args):
    with open(args.input) as file:
        data = yaml.load(file.read(), Loader=yaml.SafeLoader)
    return data


# Hide Selenium running in brosheeter when running script


def setupHeadlessChrome(args):
    chrome_options = ChromeOptions()
    if not args.visible:
        chrome_options.add_argument("--headless")
    brosheeter = webdriver.Chrome(
        executable_path="chromedriver", options=chrome_options)

    return brosheeter


def loginToPage(brosheeter, url):
    logger.info('Logging into %s', url)

    brosheeter.get(url)

    # This will await the first load on the login page, based on that 'maincontent' is drawn
    WebDriverWait(brosheeter, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.ID, "maincontent"))
    )

    # Time to collect some user info. "input" can be useful here
    # username = h@neverbland.com
    # password = Password1

    # Here we do find the first input element and inputs some text into it
    usernameElement = brosheeter.find_element_by_name("userNameOrEmail")
    passwordElement = brosheeter.find_element_by_name("password")

    usernameElement.send_keys('h@neverbland.com')
    passwordElement.send_keys('Password1')

    # Accept the cookies
    brosheeter.find_elements_by_xpath(
        "//button//*[contains(text(), 'Accept')]")[0].click()
    WebDriverWait(brosheeter, 10).until_not(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Accept')]"))
    )

    # Press the login button
    brosheeter.find_elements_by_xpath(
        "//button//*[contains(text(), 'Log in')]")[0].click()
    WebDriverWait(brosheeter, 10).until_not(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Log in')]"))
    )

# Detect element on landing page after log in


def awaitFirstDrawOnPage(brosheeter):
    WebDriverWait(brosheeter, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Hi')]"))
    )


# Detect whether Axe should be run with log in details or not


def processPages(args, data):
    results = []
    for page in data['pages']:
        brosheeter = setupHeadlessChrome(args)
        if page.get('require_login'):
            loginToPage(brosheeter, data['login']['url'])
            awaitFirstDrawOnPage(brosheeter)
        results.append(runAxeReport(brosheeter, args, page))
        closeBrosheeter(brosheeter)
    return results

# Run Axe from the command line


def runAxeReport(brosheeter, args, page):
    logger.info("Running Axe against %s", page['url'])
    pageUrl = page['url']
    brosheeter.get(pageUrl)
    axe = Axe(brosheeter)
    # Inject axe-core javascript into page
    axe.inject()
    # Run axe accessibility checks
    results = axe.run()
    return results


def closeBrosheeter(brosheeter):
    brosheeter.quit()

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

    def as_text(value):
        if value is None:
            return ""
        return str(value)

    ''' Create a new blank Workbook to record flagged items '''
    wb = openpyxl.Workbook() 
    
    ''' Get workbook active sheet '''
    ws = wb.active 

    ''' Write to the cells '''     
    ws.append(["Count", "Priority", "Title", "Description", "More info"])

    for p in problems:
        ws.append([p.count, p.impact, p.help, p.description, p.helpUrl])
    
    ''' Set the width of rows to fit text '''
    for column_cells in ws.columns:
        length = max(len(as_text(cell.value)) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column].width = length

    # Create loop to set height of rows

    header = Font(color='00FF0000', bold=True)

    ''' Enumerate the cells in the first row '''
    for cell in ws["1:1"]:
        cell.font = header
    
    ''' Save the file '''
    wb.save('report.xlsx') 


''' Execute main only if script is being executed, not imported '''
if __name__ == '__main__':
    main()
