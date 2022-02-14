import sys
import requests
from bs4 import BeautifulSoup
import re
import time
import js2py
import json
import base64
import hashlib
import pymysql
from urllib import parse

import server


#禁用安全请求警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

s = requests.session()
req_header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7'
}

db = pymysql.connect(host="localhost",user="hpu_xyzs_system",password="NY7W75JpjdGt4yAD",database="hpu_xyzs_system")
cursor = db.cursor()


def get_vpnCookies():
    # SELECT name,height FROM tb_students_info
    # -> WHERE height=170;
    sql = """
    select content from eams_session where user_id=208
    """
    cursor.execute(sql)
    data = cursor.fetchall()[-1][0]
    data = json.loads(parse.unquote(data))
    s = requests.session()
    s.cookies.update(data)
    # s.get('https://webvpn.hpu.edu.cn/', headers=dict(req_header))
    wv = s.get('https://webvpn.hpu.edu.cn/Main/index', headers=dict(req_header))
    # print('华域WebVPN' in wv.text)
    # print(wv.text)
    if '华域WebVPN' in wv.text:
        return data
    else:
        from extend import auto_login_zhhq
        auto_login_zhhq.get_session()
        return get_vpnCookies()


