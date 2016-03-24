import json
import requests
import re
from sys import stderr, exit

def fetch(number, cookie):
    url = 'https://mis.cc.ntu.edu.tw/suggest/asp/show.asp?sn=%s' % number
    request = requests.get(url, cookies=cookie)
    request.encoding = 'big5'
    return request.text

def search_one(pattern, string):
    match = re.search(pattern, string)
    if match is not None:
        match = match.group(1)
    return match

def parse(text):
    if r'<td width="100%">無此篇建議案</td>' in text:
        return { 'error': 'not_found' }
    elif r'<td width="100%">無權調閱此篇建議案</td>' in text:
        return { 'error': 'unauthorized' }

    number = search_one(r'金玉集</a> \| 第 (\d+) 則建言', text)
    if not number:
        stderr.write('Cannot parse text properly, see if cookie expired')
        raise Exception('Parse failed')
    
    return {
        'number': number
    }

try:
    with open('cookie.json', 'r') as f:
        cookie = json.load(f)
except IOError:
    stderr.write('Cookie file not found')
    exit(-1)

print(parse(fetch(8845, cookie=cookie)))
