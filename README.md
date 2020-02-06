This script is for the automation of data extraction from accessibility reports with Axe or Lighthouse, which is autogenerated after the input of a specified list of URLs. This script extracts only the required data from this report and exports it into a spreadsheet for better readability by the development team.

# Set up

1. Create a virtual environment with `virtualenv -p python3 env`
2. Activate the virtualenv with `source env/bin/activate`
3. Install requirements with `pip install -r requirements.txt`
4. Install Chromedrivers with Brew with `brew cask install chromedriver`

# Run script

1. Activate the virtualenv with `source env/bin/activate`
2. Run the script with `python AxeReportGenerator.py [yaml file]`

## Required parameters

- Your `[yaml file]` should contain all the URLs you want to run against the script
- Should any URL require cookies, you will need to add `require_login: true` to each URL

### Yaml file structure example

```yaml
pages:
  - url: https://account.develop.bigwhitewall.com/log-in
  - url: https://develop.bigwhitewall.com/
    require_login: true
```

## Flags

- Appending `--visible` to the command in the shell runs the script with a visible browser
- Appending `--standard` to the command in the shell allows you to choose which WCAG standard to run the script against: either `wcag2a` or `wcag2aa` - running without stating which standard will run the script against all accessibility standards Axe has to offer
- Appending `--package` to the command in the shell allows you to choose which accessibility tool to run the script against: either `axe` or `lighthouse` - this is a required argument that you must specify
