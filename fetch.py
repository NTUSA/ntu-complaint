import json
import requests
import re
from sys import stderr, exit

def fetch(number, cookie):
    url = 'https://mis.cc.ntu.edu.tw/suggest/asp/show.asp?sn=%s' % number
    request = requests.get(url, cookies=cookie)
    request.encoding = 'big5'
    return request.text

try:
    with open('cookie.json', 'r') as f:
        cookie = json.load(f)
except IOError:
    stderr.write('Cookie file not found')
    exit(-1)

print(fetch(8845, cookie=cookie))
