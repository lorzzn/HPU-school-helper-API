

from urllib import parse
from flask import jsonify
from controller.confutil import *
from exception import BaseException

zhhq_base_url = 'https://uia.hpu.edu.cn'


def get_session(ip):

    s = requests.session()

    header = dict(req_header)
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'
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

    # print(d_session)
    # print(lt)
    # print(execution)
    # print(token)
    # print("data:image/jpeg;base64,%s"%b64)

    return {
        'content': parse.quote(d_session),
        'lt': lt,
        'execution': execution,
        'token': token,
        'captcha': "data:image/jpeg;base64,%s"%b64,
        'captchaHtml': f"<img src='data:image/jpeg;base64,{b64}'></img>"
    }


def login_zhhq(session, username, password, captcha, lt, execution, token, ip):

    loginUrl = f"{zhhq_base_url}/cas/login#/"

    s = requests.session()
    s.cookies.update(json.loads(session))

    u = username
    p = password

    header = req_header
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'
    
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
        raise BaseException.APIException(msg='密码错误', error_code=20001)

    if "login." in dologin.text:
        raise BaseException.APIException(msg='验证码错误', error_code=20002)

    burl = "http://zhhq.hpu.edu.cn/redirect/main/user/statistics"

    Tindex_page = s.get(burl, headers=header)
    redUrl = re.findall("top.location.href='(.*?)'",Tindex_page.text)[0]

    s.get(redUrl, headers=
    # header
    {
        # "Host": "zhhq.hpu.edu.cn",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "http://zhhq.hpu.edu.cn/redirect/main/user/statistics",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    ,verify=False)

    index_page = s.get(burl, headers=header)

    ip_soup = BeautifulSoup(index_page.text, "html.parser")
    # print(ip_soup)
    avatar = ip_soup.find(attrs={"class":"Head_portrait"}).findChildren()[0].get("src").strip()
    nickname = ip_soup.find(attrs={"class":"userName"}).string
    academy = ip_soup.find(class_="information_text").findChildren()[0].get("title")
    dorm = ip_soup.find(class_="information_text").findChildren()[1].get("title")

    d = {}
    d["avatar"] = avatar
    d["nickname"] = nickname
    d["academy"] = academy
    d["dorm"] = dorm

    scookie = s.cookies.get_dict()
    d["session"] = parse.quote(json.dumps(scookie, ensure_ascii=False))

    # print(json.dumps(d, ensure_ascii=False))
    return d










