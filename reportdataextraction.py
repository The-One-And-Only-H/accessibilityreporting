import json

with open('report.json') as f:
    data = json.load(f)

audits = data['audits']

for audit_name, audit in audits.items():
    if audit['score'] != None and audit['score'] <= 0:
        print(audit['title'], audit['description'])
