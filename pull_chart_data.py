# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "gspread~=6.2"
# ]
# ///

import json
import os

import gspread

from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    credentials = os.getenv('GDOC_CREDENTIALS')
    if not credentials:
        raise ValueError("GDOC_CREDENTIALS environment variable is not set")
    
    service_acct = json.loads(credentials)

    gc = gspread.service_account_from_dict(service_acct)

    today = datetime.now(ZoneInfo('America/New_York'))

    sh = gc.open('published crosswords')
    puzzles = sh.worksheet('all').get_all_records()

    for r in puzzles:
        r['date'] = datetime.strptime(r['publish date'], '%m/%d/%Y').date().isoformat()
        r.pop('payment')
        r['category'] = 'puzzle'

 
    puzzles = [r for r in puzzles if datetime.fromisoformat(r['date']).replace(tzinfo=ZoneInfo('America/New_York')) <= today]

    misc = sh.worksheet('misc').get_all_records()

    for r in misc:
        r['date'] = datetime.strptime(r['publish date'], '%m/%d/%Y').date().isoformat()
        r['category'] = 'misc'

    misc = [r for r in misc if datetime.fromisoformat(r['date']).replace(tzinfo=ZoneInfo('America/New_York')) <= today]

    data = puzzles + misc
    data.sort(key=lambda e: e['date'], reverse=True)

    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    main() 
