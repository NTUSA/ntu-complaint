#!/usr/bin/env python
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

def print_err(text, color=Style.RESET_ALL, bright=False):
    if bright:
        stderr.write(Style.BRIGHT)
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
        print_err('ERR: Cannot parse text properly, see if cookie expired.', Fore.RED, bright=True)
        print_err('Original string:')
        print_err(text, Fore.WHITE, bright=True)
        print_err('\n')
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
    import argparse
    from sys import stdout, exit

    def load_json(filename):
        with open(filename, 'r') as f:
            return json.load(f)

    parser = argparse.ArgumentParser(description='Fetch and parse campus suggestions.')
    parser.add_argument('-s', '--save', action='store_true', help='Stores the parsed information to file.')
    parser.add_argument('-c', '--cookie', type=load_json, default='cookie.json', help='Cookie file to use. (default: cookie.json)')

    group = parser.add_argument_group(title='Batch operation', description='Specifies a range of suggestion IDs.')
    group.add_argument('-f', '--from', type=int, metavar='id', dest='start', help='Starting ID, inclusive.')
    group.add_argument('-t', '--to', type=int, metavar='id', dest='stop', help='Ending ID, inclusive.')

    parser.add_argument('id', nargs='*', type=int, help='Suggestion ID(s) to acquire.')

    args = parser.parse_args()

    if args.start and args.stop:
        ids = range(args.start, args.stop + 1)
    elif args.id:
        ids = args.id
    else:
        parser.print_help()
        exit()

    respond_count, empty_count, unauthorized_count, non_existent_count = (0, 0, 0, 0)
    for number in ids:
        text = fetch(number, args.cookie)
        data = parse(text)

        if args.save:
            # Count statistics
            if data.get('error') == 'unauthorized':
                unauthorized_count += 1
            elif data.get('error') == 'not_found':
                non_existent_count += 1
            elif not data['response'] or not data['complaint']:
                empty_count += 1
                print_err('WARN: Suggestion #%s is empty' % number, Fore.YELLOW, bright=True)
            else:
                respond_count += 1

            # Save file
            with open('files/%s.json' % number, 'w') as output:
                json.dump(data, output, ensure_ascii=False, indent='\t')

        else:
            json.dump(data, stdout, ensure_ascii=False, indent=2)

    # Print statistics if available
    if args.save:
        print('Statistics:\n')
        print('  Responses:    \t%s%s%s' % (Style.BRIGHT if respond_count else Style.DIM, respond_count, Style.RESET_ALL))
        print('  With warnings:\t%s%s%s' % (Style.BRIGHT + Fore.YELLOW if empty_count else Style.DIM, empty_count, Style.RESET_ALL))
        print('  Unauthorized: \t%s%s%s' % (Style.BRIGHT + Fore.RED if unauthorized_count else Style.DIM, unauthorized_count, Style.RESET_ALL))
        print('  Non-existent: \t%s%s%s' % (Style.BRIGHT + Fore.RED if non_existent_count else Style.DIM, non_existent_count, Style.RESET_ALL))

        total = (respond_count + empty_count + unauthorized_count + non_existent_count)
        print('')
        print('  Total responses:\t%s\n' % total)
