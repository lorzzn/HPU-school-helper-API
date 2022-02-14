
import json
import requests 
import pymysql, time
from bs4 import BeautifulSoup
from urllib import parse

CONFIG = {
    'App_key': 'SrqvQHYRwjmmClFyDkiv3XQL',
    'Secret_Key': 'n9ldvaTWI5DTq2ECqOxHrAqUCd2YtOzC',
    'Uia_Account': '311804030207',
    'Uia_Pass': 'lzp032433'
}

req_header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7'
}

zhhq_base_url = 'https://uia.hpu.edu.cn'


# 208 - Fine

# 打开数据库连接
db = pymysql.connect(host="localhost",user="hpu_xyzs_system",password="NY7W75JpjdGt4yAD",database="hpu_xyzs_system")
 
# 使用cursor()方法获取操作游标 
cursor = db.cursor()

def write_log(content:str):
    import time
    log = open('auto_login_zhhq_log.txt', 'a')
    log.writelines(f'[ {int(time.time())} ] - {content}')
    log.close()

def update_session(content):
    # sql删除
    delete_sql = """
    DELETE FROM eams_session WHERE user_id = '208' 
    """
    # SQL 插入
    sql = f"""
    INSERT INTO eams_session(user_id, content,  create_time) 
    VALUES("208", "{content}", "{int(time.time())}")
    """
    print(content)
    try:
        # 执行sql语句
        cursor.execute(delete_sql)
        cursor.execute(sql)
        # 提交到数据库执行
        db.commit()
        return True
    except:
        # 如果发生错误则回滚
        db.rollback()
        return False

def calc(img_base64: str):
    """
    根据传入的图片计算值并返回
    :param img_base64: 图像数据，base64编码后进行urlencode，需去掉编码头（data:image/jpeg;base64,)
    :return: int: 计算后的数值
    """
    s = requests.session()

    # 请求`access_token` 
    oauth_url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=" + CONFIG['App_key'] + "&client_secret=" + CONFIG['Secret_Key']

    token = s.get(oauth_url).json()['access_token']

    # 通用文字识别 如果你觉得识别错误率比较高，请将下面一行注释掉，将高精度识别的注释打开
    api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic" + "?access_token=" + str(token)
    # 高精度识别
    # api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic" + "?access_token=" + str(token)

    header = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'image': str(img_base64)
    }
    # response like {'words_result': [{'words': '1+5=?'}], 'log_id': 1383448933996429312, 'words_result_num': 1}
    ocr = s.post(api_url, headers=header, data=data)
    # print(ocr.json()['words_result'][0])
    return eval(ocr.json()['words_result'][0]['words'][0:3])


def get_session(ip='47.103.223.186'):

    s = requests.session()
    # ip = ip if ip else '47.103.223.186'

    header = dict(req_header)
    header['X-Forwarded-For'] = ip 
    loginUrl = f"{zhhq_base_url}/cas/login#/"
    captchaUrl = f"{zhhq_base_url}/sso/apis/v2/open/captcha"

    login = s.get(loginUrl, headers = header)
    l_soup = BeautifulSoup(login.text, "html.parser")
    lt = l_soup.find(attrs={'name': "lt"}).get("value")
    execution = l_soup.find(attrs={'name': "execution"}).get("value")

    getCaptcha = s.get(captchaUrl, headers = header)
    resJSON = json.loads(getCaptcha.text)
    b64 = "".join(resJSON['img'].split())   
    token = "".join(resJSON['token'].split())   

    d_session = json.dumps(s.cookies.get_dict()) # session

    # print(lt)


    return login_zhhq(
        d_session, 
        '311804030207', 
        'lzp032433', 
        b64, 
        lt, 
        execution, 
        token, 
        ip
    )

def login_zhhq(session, username, password, captcha, lt, execution, token, ip):

    loginUrl = f"{zhhq_base_url}/cas/login#/"

    s = requests.session()
    # print(session)
    s.cookies.update(json.loads(session))

    u = username
    p = password

    header = req_header
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    captchab64 = captcha
    captcha = calc(captcha)
    print(captcha)
    
    formdata = {
        "username": u,
        "password": p,
        "captcha":captcha,
        "token":token,
        "_eventId": "submit",
        "lt": lt,
        "source": "cas",
        "execution": execution
    }

    dologin = s.post(loginUrl, data=formdata, headers=header)
    # print(dologin.text)
    if "密码错误" in dologin.text:
        write_log(
            '密码错误' + '\n' + \
            captchab64 + '\n' + \
            str(dict(formdata))
        )

    if "login." in dologin.text:
        write_log(
            '验证码错误' + '\n' + \
            captchab64 + '\n' + \
            str(dict(formdata))
        )

    # d = {}
    webv = s.get('https://webvpn.hpu.edu.cn/', headers=header)
    # tc = s.get('https://webvpn.hpu.edu.cn/http/218.196.240.21/tycsweb/dimage.aspx', headers=header)
    # print(webv.text)
    # print(tc.text)
    scookie = s.cookies.get_dict()
    _session = parse.quote(json.dumps(scookie, ensure_ascii=False))

    # print(json.dumps(d, ensure_ascii=False))
    return update_session(_session)

# get_session()







