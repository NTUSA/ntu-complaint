import html
import json
import requests
import re
from colorama import Fore, Style
from sys import stderr

def fetch(number, cookie):
    url = 'https://mis.cc.ntu.edu.tw/suggest/asp/show.asp?sn=%s' % number
    request = requests.get(url, cookies=cookie)
    request.encoding = 'big5'
    return request.text

def search_one(pattern, string):
    match = re.search(pattern, string)
    if match is not None:
        match = match.group(1).strip()
    return match

def search_multiline(pattern, string):
    match = re.search(pattern, string)
    if match is not None:
        match = html.unescape(match.group(1).replace('<br>', '\n')).strip()
    return match

def print_err(text, color=Style.RESET_ALL):
    stderr.write(color)
    stderr.write(text)
    stderr.write('\n')

def parse(text):
    if r'<td width="100%">無此篇建議案</td>' in text:
        return { 'error': 'not_found' }
    elif r'<td width="100%">無權調閱此篇建議案</td>' in text:
        return { 'error': 'unauthorized' }

    number = search_one(r'金玉集</a> \| 第 (\d+) 則建言', text)
    if not number:
        print_err('Cannot parse text properly, see if cookie expired', Fore.RED + Style.BRIGHT)
        print_err(text, Fore.WHITE)
        print_err('\n\n')
        raise Exception('Parse failed')

    return {
        'number': number,
        'identity': search_one(r'建議者身份</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
        'category': search_one(r'建議議題類別</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
        'subject': search_one(r'主旨</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
        'complaint': search_multiline(r'建議內容</strong></td>\s*<td[^>]*>(.+?)</td>', text),

        'status': search_one(r'處理情形</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
        'responder': search_one(r'回覆單位</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
        'response': search_multiline(r'回覆內容</strong></td>\s*<td[^>]*>(.+?)</td>', text),
        'date': search_one(r'回覆時間</strong></td>\s*<td[^>]*>([^<]+)</td>', text),
    }

if __name__ == '__main__':
    from sys import argv, exit

    try:
        with open('cookie.json', 'r') as f:
            cookie = json.load(f)
    except IOError:
        print_err('Cookie file not found', Fore.RED)
        exit(-1)

    if len(argv) < 2:
        # Default action
        print('Usage: python fetch.py <number>')
    elif len(argv) == 2:
        number = int(argv[1])
        print(parse(fetch(number, cookie=cookie)))
