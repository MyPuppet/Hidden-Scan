# -*- coding: utf-8 -*-
# @Time    : 2017/12/5 下午2:02
# @Author  : MyPuppet
# @File    : Giveway.py
# @Software: PyCharm
import re
import pymongo
import requests
from requests.exceptions import RequestException
from pyquery import PyQuery as pq
from multiprocessing import Pool

client = pymongo.MongoClient('127.0.0.1', connect=False)
gdb = client['giveway']['result']

first_url = 'http://top.chinaz.com/all/index.html'
base_url = 'http://top.chinaz.com/all/index_{}.html'


def get_url(page_number):
    if page_number == 1:
        return first_url
    return base_url.format(page_number)


def get_html(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            return response.text
        return None
    except RequestException:
        get_html(url)


def parse_html(html):
    doc = pq(html)
    items = doc('ul.listCentent .CentTxt').items()
    for item in items:
        title = item('.rightTxtHead a').text()
        url = 'http://' + item('.rightTxtHead span').text()
        img_src = item('.RtCPart .RtCData a img').attr('src')
        weight = re.search('\d+', img_src).group()
        yield {
            'title': title,
            'url': url,
            'weight': weight
        }


def get_check_url(url):
    dic = [
        '.git/HEAD',
        '.svn/entries',
        '.DS_Store',
        '.svn/wc.db'
    ]
    for i in range(len(dic)):
        yield url + '/' + dic[i]


def check(url, weight, title):
    headers = {'User-Agent': 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;360SE)'}
    for item in get_check_url(url):
        try:
            response = requests.get(item, headers=headers, timeout=10)
            response.encoding = response.apparent_encoding
            if response.status_code == 200 or response.status_code == 403:
                if not response.text.lower().strip().startswith('<!doct') and not response.text.lower().startswith(
                        '<html') and response.text.lower().strip() != '':
                    data = {
                        'url': item,
                        'title': title,
                        'content': response.text[:1000],
                        'weight': weight
                    }
                    if gdb.insert(data):
                        print('###{}探测成功'.format(item))
        except RequestException:
            print('!!!{}请求失败'.format(item))


def main(page_number):
    url = get_url(page_number)
    html = get_html(url)
    if (html):
        for item in parse_html(html):
            print('检测:', item['url'])
            check(item['url'], item['weight'], item['title'])


if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [i for i in range(2, 1801)])
