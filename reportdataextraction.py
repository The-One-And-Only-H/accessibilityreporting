import subprocess
import json
import sys
import csv

# Runs URL against Lighthouse in command line, which outputs as a JSON file in memory
url = sys.argv[1]
data = subprocess.check_output(
    ["./node_modules/.bin/lighthouse", url, "--output", "json"])

data = json.loads(data)

audits = data['audits']

# Writes flagged items as CSV file
w = csv.writer(sys.stdout)

for audit_name, audit in audits.items():
    if audit['score'] != None and audit['score'] <= 0:
        w.writerow([audit['title'], audit['description']])
