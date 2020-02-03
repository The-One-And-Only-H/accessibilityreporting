import logging

import yaml

from openpyxl import Workbook
from openpyxl.styles import Font

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as SeleniumExpectedConditions
from selenium.webdriver.common.by import By

from axe_selenium_python import Axe

from argparse import ArgumentParser

'''Log more information messages to the shell'''
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
            problem.urls.append(result['url'])

    def getSummary(self):
        return self.problems

class Problem:
    def __init__(self, impact, help, description, helpUrl):
        self.impact = impact
        self.help = help
        self.urls = []
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

def parseCommandLine():
    '''
    Optional arguments to:
    - See the script running in the browser
    - Choose an accessibility standard to test against
    - Pass which URLs you want to test
    '''
    parser = ArgumentParser()
    parser.add_argument('--visible', action='store_true',
                        help='display browser')
    standards = ['wcag2a', 'wcag2aa']
    parser.add_argument('--standard', choices=standards, 
                        metavar='NAME', 
                        help='choose which standard to test against (choices: %s, default: all)' % ', '.join(standards))
    parser.add_argument(
        'input', help='runs script against chosen list of URLs')
    args = parser.parse_args()
    return args

'''Loads data from yaml file passed through the command line'''
def loadInputFile(args):
    with open(args.input) as file:
        data = yaml.load(file.read(), Loader=yaml.SafeLoader)
    return data

def setupHeadlessChrome(args):
    '''Hide Selenium running in browser when running script'''
    chrome_options = ChromeOptions()
    if not args.visible:
        chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(
        executable_path="chromedriver", options=chrome_options)

    return browser

def loginToPage(browser, url):
    logger.info('Logging into %s', url)

    browser.get(url)

    '''This will await the first load on the login page, based on that 'maincontent' is drawn'''
    WebDriverWait(browser, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.ID, "maincontent"))
    )

    '''Time to collect some user info. "input" can be useful here'''
    '''username = h@neverbland.com'''
    '''password = Password1'''

    '''Here we do find the first input element and inputs some text into it'''
    usernameElement = browser.find_element_by_name("userNameOrEmail")
    passwordElement = browser.find_element_by_name("password")

    usernameElement.send_keys('h@neverbland.com')
    passwordElement.send_keys('Password1')

    '''Accept the cookies'''
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Accept')]")[0].click()
    WebDriverWait(browser, 10).until_not(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Accept')]"))
    )

    '''Press the login button'''
    browser.find_elements_by_xpath(
        "//button//*[contains(text(), 'Log in')]")[0].click()
    WebDriverWait(browser, 10).until_not(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//button//*[contains(text(), 'Log in')]"))
    )

def awaitFirstDrawOnPage(browser):
    '''Detect element on landing page after log in'''
    WebDriverWait(browser, 10).until(
        SeleniumExpectedConditions.presence_of_element_located(
            (By.XPATH, "//h2[contains(text(), 'Hi')]"))
    )

def processPages(args, data):
    '''Detect whether Axe should be run with log in details or not'''
    results = []
    for page in data['pages']:
        browser = setupHeadlessChrome(args)
        if page.get('require_login'):
            loginToPage(browser, data['login']['url'])
            awaitFirstDrawOnPage(browser)
        results.append(runAxeReport(browser, args, page))
        closeBrowser(browser)
    return results

def runAxeReport(browser, args, page):
    '''Run Axe from the command line'''
    logger.info("Running Axe against %s", page['url'])
    pageUrl = page['url']
    browser.get(pageUrl)
    axe = Axe(browser)
    '''Inject axe-core javascript into page'''
    axe.inject()
    '''Run axe accessibility checks'''
    if args.standard == 'wcag2a':
        logger.info('Collating wcag2a results')
        axe_options = {"runOnly": {"type": "tag", "value": ["wcag2a"]}}
        results = axe.run(options=axe_options)
    elif args.standard == 'wcag2aa':
        logger.info('Collating wcag2aa results')
        axe_options = {"runOnly": {"type": "tag", "value": ["wcag2aa"]}}
        results = axe.run(options=axe_options)
    else:
        logger.info('Collating all results')
        results = axe.run()
    results['url'] = page['url']
    return results

def closeBrowser(browser):
    browser.quit()

def aggregateResults(results):
    '''Filter through problems flagged by the Axe report and collate duplicates'''
    ag = ProblemAggregator()
    for result in results:
        ag.addResult(result)
    return ag.getSummary()

def emitResults(summary):
    '''Create CSV file ordering collated data by count then alphabetically'''
    problems = list(summary.values())

    def getCount(p):
        '''Sort problems in order of highest occurrence to lowest'''
        return p.count

    problems.sort(key=getCount, reverse=True)

    def toString(value):
        if value is None:
            return ""
        return str(value)

    def listToString(s):  
    
        '''Initialise empty string'''
        stringify = " " 
        stringify = " " + "\n"

        return stringify.join(s)

    ''' Create a new blank Workbook to record flagged items '''
    workbook = Workbook() 
    
    worksheet = workbook.active 

    ''' Write to the cells '''     
    worksheet.append(["Count", "Priority", "URLS", "Title", "Description", "More info"])

    for p in problems:
        worksheet.append([p.count, p.impact, listToString(p.urls), p.help, p.description, p.helpUrl])
    
    ''' Set the width of rows to fit text '''
    for column_cells in worksheet.columns:
        length = max(len(toString(cell.value)) for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column].width = length
        worksheet.column_dimensions[column_cells[0].column].height = length

    header = Font(color='00FF0000', bold=True)

    ''' Enumerate the cells in the first row '''
    for cell in worksheet["1:1"]:
        cell.font = header
    
    ''' Save the file '''
    workbook.save('report.xlsx') 


''' Execute main only if script is being executed, not imported '''
if __name__ == '__main__':
    main()
