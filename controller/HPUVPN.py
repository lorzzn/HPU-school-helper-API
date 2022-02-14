
import os
from flask.wrappers import JSONMixin
import img2pdf
import pypandoc
# import subprocess
import base64
# import patoolib
from bs4 import element
from PIL import Image
from urllib import parse
from flask import jsonify
from controller.confutil import *
from exception import BaseException
from controller.common import *
# 加密库
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Crypto.PublicKey import RSA

mobile_h = {
        # 'Host': 'webvpn.hpu.edu.cn',
        # 'Connection': 'keep-alive',
        # 'Cache-Control': 'max-age=0',
        # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        # 'sec-ch-ua-mobile': '?0',
        # 'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84',
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        # 'Sec-Fetch-Site': 'none',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-User': '?1',
        # 'Sec-Fetch-Dest': 'document',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        # 'Referer': 'https://webvpn.hpu.edu.cn/Main/historyindex'
    }

base_url = "https://webvpn.hpu.edu.cn/"

def login_hpu_vpn(jwzh, jwmm, ip):

    s = requests.session()
    s.cookies.update({
        'language' : 'zh_CN',
        'sms_timeout' : '0'
    })

    baseurl = "https://vpn.hpu.edu.cn/por/login_psw.csp?encrypt=0"
    
    mobile_header = dict(mobile_h)
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    formData = {
        "svpn_name": jwzh,
        "svpn_password": jwmm
    }

    pg = s.post(baseurl, data=formData, headers=mobile_header, verify = False, allow_redirects=False)
    # print(pg.text)
    cok = s.cookies.get_dict()

    if "ENABLE_RANDCODE" not in cok:
        raise BaseException.APIException(msg='密码错误', error_code=30001)

    s.get(base_url + "http/218.196.240.155/swfweb/hpugg.aspx", headers= mobile_header, verify = False, allow_redirects=False)

    # print(json.dumps(s.cookies.get_dict(), ensure_ascii=False))
    session = json.dumps(s.cookies.get_dict(), ensure_ascii=False)

    return session


def school_ann(session, page, ip):
        
    aurl = base_url + "http/218.196.240.155/swfweb/hpugg.aspx"

    header = mobile_h
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    # 更新session
    if session:
        s.cookies.update(json.loads(session)) # 读取
    s.cookies.update(get_vpnCookies())
    # print(s.cookies.get_dict())

    # 请求页面
    # print(aurl+"?text=&page="+parse.quote(str(page))+"\n>>>>>>>>>>>")
    res = s.post(aurl+"?text=&page="+parse.quote(str(page)),headers=header, verify = False)
    print(res.text, res.status_code)
    if res.status_code != 200:
        raise BaseException.APIException(msg='登录超时，请重新登录', error_code=30002)

    res_soup = BeautifulSoup(res.text, "html.parser")
    maxpage = res_soup.find_all("span", {"id": "Label4"})[0].string
    annnum = res_soup.find_all("span", {"id": "Label1"})[0].string

    ahrefs = res_soup.find_all("a", {"href": re.compile("hpugm.*?id=.*")})

    print(ahrefs)

    datalist = []
    for i in ahrefs:
        d = {}
        q = i.contents
        w = i.get("href")
        e = i.parent.previous_sibling.string.strip()
        d["id"] = re.findall("id=(.*)", w)[0]
        d["title"] = q[0]
        d["date"] = e
        d["isTop"] = 1 if len(q)>1 else 0
        datalist.append(d)

    out = {}
    out["annNum"] = annnum
    out["hasNext"] = 1 if int(maxpage)>int(page) else 0
    out["data"] = datalist

    print(json.dumps(out, ensure_ascii=False))
    return out


def school_ann_download(session, ann_id):
    
    # requests.urllib3.disable_warnings()
    def mkdirW(path):
        isExis = os.path.exists(path)
        if not isExis:
            os.makedirs(path)

    def get_ann_list(ann_dir, url_prefix='', remove_str=''):
        key = 'school_anns_' + ann_dir + '_' + url_prefix + '_' + remove_str
        # print(key)
        with server.app.app_context():
            cached_list = server.cache.get(key)
            if cached_list:
                return cached_list
        result = []
        f_list = list_dir(ann_dir, [])
        # print(f_list)
        for f in f_list:
            # fn = f.split('/')[-1:][0]
            # fn = f
            result.append({
                'name': f.split('/')[-1:][0],
                'size': os.path.getsize(f),
                'url': url_prefix + f.replace(remove_str, '')
            })
        with server.app.app_context():
            server.cache.set(key, result, timeout=60*60*24)
        return result
    

    aid = ann_id
    rootdir = "/www/wwwroot/HPU_xyzs_static/public/sources/anns"
    tempdir = '/www/wwwroot/HPU_xyzs_static/public/sources/temp'
    itemdir = rootdir +'/'+ aid

    file_base_url = "https://static.hpubox.top/"
    file_webroot = '/www/wwwroot/HPU_xyzs_static/'

    respons = {
        'msg': 'success',
        'data': list
    }

    if os.path.exists(itemdir) and len(os.listdir(itemdir)) > 0:
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        respons['g'] = True
        return respons


    aurl = base_url + "http/218.196.240.155/swfweb/hpugm.aspx?id="+aid

    # 更新session
    s = requests.session()
    if session:
        s.cookies.update(json.loads(session)) # 读取
    s.cookies.update(get_vpnCookies())

    res = s.get(aurl, verify = False)

    if res.status_code != 200:
        raise BaseException.APIException(msg='获取公告内容失败，可能需要重新登录', error_code=30003)

    fUrl = parse.unquote(res.url)
    fName = fUrl.split("/")[-1:][0]
    fType = fUrl.split(".")[-1:][0]

    mkdirW(itemdir)

    if fType.lower() in ["doc","docx","xls","xlsx","ppt","pptx","pdf"]:
        with open(itemdir +'/'+ fName, "wb") as f:
            f.write(res.content)
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons

    if fType.lower() in ["rtf"]:
        with open(itemdir +'/'+ fName + ".doc", "wb") as f:
            f.write(res.content)
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons

    if fType.lower() in ["jpg","jpeg","gif","png"]:
        tempfile = tempdir +'/'+ fName
        # print(tempfile)
        with open(tempfile, "wb") as d:
            d.write(res.content)
        with open(itemdir +'/'+ fName + ".pdf", "wb") as f:
            i = Image.open(tempfile)
            i = i.convert("RGB")
            i.save(tempfile)
            f.write(img2pdf.convert(tempfile))
            os.remove(tempfile)
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons
    
    # if fType.lower() in ["html", "htm"] and res.status_code == 200:
    if ("html" in fType.lower() or "htm" in fType.lower()) and res.status_code == 200:
        pypandoc.convert_text(res.text, "docx", "html", outputfile=itemdir + "/公告内容.docx")
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons

    if fType.lower() in ["zip", "7z", "rar"]:
        with open(itemdir +'/'+ fName, "wb") as f:
            f.write(res.content)
        force_dir_7zr(itemdir)
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons

    if "aspx" in fType.lower() and res.status_code == 200:
        # print(rootdir+aid+"/公告内容.docx")
        pypandoc.convert_text(res.text, "docx", "html", outputfile=itemdir + "/公告内容.docx")
        respons['data'] = get_ann_list(itemdir, file_base_url, file_webroot)
        return respons


def school_lectures(session, page, ip):

    return False
    
    # 更新session
    s = requests.session()
    if session:
        s.cookies.update(json.loads(session))
    s.cookies.update(get_vpnCookies())

    aurl = base_url + "http/218.196.240.155/swfweb/hpugg.aspx"
    header = dict(mobile_h)
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    form = {
        "__EVENTTARGET": "GridView1$ctl06$btnGo",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "Yw2pXpk78bUX5YPAohR/ZVg4v9aJB1PPzM005In+bTh4CPTmULkjLOSiKnAQB1X8D3Orbod6CHYQytSIMuuVUv1hN+IXlP53bL8VqjOcM5MhiJ8u9o1JziTSmhTpKCpz8tmsjVJDmAq6ENWEWuTuM16PuUAGb+IH0Q79yjTjtutumhQEx/XyZL8z2rCmlcUt4BrfrIusj8yL6W5g17ckkuuNdkDzaCmhfsgY4vGIIX7+G8oM3uKHPv5qnXvMBMCPeNcupl94a97SjZObN8j73z9kjfRaqbGqlhfHSGJqzAGLO4sg7wu+XALNff6TxofWMj9WPcZ7knvAHJ/BcQ+d13P/JlOupKr1HwpYWOKVse/xWRxEeymt8ZCBXUUty9sZy1gATQtjDAhSKsn1Sgz6TFc7XY4mHv8ZM4l+A8NnExzarwINmWP5UDf/LeA08n3YqiIE2DIcfHdFhqngTVRXwMInLsP5zm5OnE3atfGzMRBNmFAdd5lcwnzesZkT5JjzdvEhIAL7XmYiQziBhPEqwOOWLInyuRP28Xmc5MR6a59tuZrwIwVKbWy2aYsVWI5ClQ12c6tknLN/Ldp/PxEx2QvQiU9XkXXWusAhWrMyW7txzLHVm1NqWEHiN8yVmAteyHMkvDpxBmjI//2whJVrBL/Ov+MzReAre5yUy4oUJ2l5TXaozLL8EczIRDHqVgqZJbct93ySeZi0NBvdg064edm4Te0XQ31eknk6XvcZGdgNJEBh5fn9L+2/DHZTVl8O/kyop077I21JPEHOPaDESvWy6n4DF30hI3ITu0jAnRsdXNaGZO8dba+aLYB39zoDYUa7PXSujBZV6resuizYx+cNC2luBIxmvCtSy9oMAS7LXpeol6JLYwAnrehGcJFZvXeDaxTrO9dHRNqU0D4QljNOTS8uVMN+lf92T4eenifmdrEldTqJlivuuPbyclpBHgMEKSm+SKVJo2ZyRs16KjnTy+PV9KSAkSEqLfMmhZ7vFjgFe88Med14qvl8qrISmanB7OmUZ8pVyF8wX1ITnsyY5tDGWYrn16sgEakTtDAX9Ll/iLso+0OTyOe2uxyAPnnw0UMMNifqaoxwJbJfwAYQ5Gv7e81Vl/cWSJY3AACNgTndkBcjfnLcN8A1pKPc/MPYQ0KfsC2+aCEi0cbHz0ItW225sNjUlEwL96gaZmEL1hFfRNFN/b74u+XhEkcZgqR+/pTd627deLvzUHJnltmBSLEwQkELnoskTuosxEigb69ZQYN/NSt2rKml+er4bIsRR6gMUtZbPn1pNuzNNMHNFdAkbrSn9CG/hhHKqpDbXROifJDIE6Dc5MEsVY97ijLQQr1CfLQzLiyvUmbni4LCTmkqOB9hKbwQn2C/sbKr6fzcu34DK6kqZCK4P0Ls9bG+8axRNs1oU6OsrAPKSenZ55rc9l5Xm7455fA4QXNHtXV3BC/N78QIg91CIWvA2CgVvrZqUyTsWweeJ0JTE44P8DQYbxUqXxvIG86HdwxALunZgwp0n/DTtbQ5m9irxtCYZaikCntYZO7sJuU3n7+gkgkzPQ6rFXYQjp/OGUrVqkza5IpriXFiL2qiwswJXZhWlaSQIRGTo9MCscxrersj1foUng+JgFDd7+4cJDlyGn0qqhpDsnwurOZMLFuU7x9iVP1I08YqJ5DOLZm4YgUlfR0sqQVR05xeSb9g4UMMgDZ0gAq+zHVszp269qZS3OX97q/uA7EU4nct6b1fGjCmAzZmKqmhZpoo0kTu5Ylio8GM+RI0ORPB3vfBN3hdQaKvWEjEyjsvnxc9BUkvgCWS/TIvCbOBv7r7tPh6ft7JmLkgRRYuCPoyrx7dNahHZODP1DuwfOhIcsqsaUgikZvCPaDRorVMo5Zllzoq69itL2zYixOqzOBP6pjSsT0MhW1zaSdWX6YzTNowa2OF/Y5xz1SI9FcwbEAVNizolGt+2tyNPtzv5eMudL1ieJYovukaRgqBFA218Yc6l781j0JN9RmZW5lh3whMweVn+dFDtrkoVXHHagjvL8CmTa2MOEpzF5Nh8npGGj8Totzo94WFNNK85DExaTk+uUALdjFcw6BpP+Q8qdD0aU/+NI48Tv+fnyBUIoE8wmKpzppCPZaQ4L2TmTL+gbgWkhvqBbOllMjfsu1obyj5Ri+WHq4rZaD66XndnS44t2QCrNDZxjnIGsE8E5uH9QIT9+Y8e2vXTrVvvpHgRUryg1R556XaE7b3DWLufX+SNyTBj3qkYDRHRciL1GTiVm0AQ/KLYp32wkg6mbmhBT90pATHR8/03HHfmfJBK9AxYjRlpJ7JFgODH08biasGxlZ3BfsgFlyxu44d0IKaBcvGZIYwNme6XzpvjDHudpfcJ4pDpiS/u/oxpa3geg+RgSGL3b5sQ4ag2qUBHmvCpxq6LccEIion2hi5nf3YksdO+Cus2b9SdmncO1lN8WDVUpZk++AklteXGJRBJe2r0FBkn0KxjfANMscjrvZN5ADwzGeuaE6rDzNt9QWpKYbYIxYpmvG4rwivmJ8p5zw71x+pCRihtjUoWrTGDtFr4FOK320UKvAs1U8dYgv4rM9ev9Oj2+Y6MIclC7bt9Evfg/C62ErzCddEXZRcWSVjkjD+nskwZvgPeavXeJWd1yZA5bVMMfpo1yXUUCvHF6pmtqyS8D8HLtZZynHHjZ91C3gY/SC4FMrtXeb+AA0V/L/9OrghZsFJWZVugd4NYajqUWux9Zzz7sQxa4h26AOK4+tfbU+LwE1OYP5hnsuExbdJ5amYdJFJsBdtBDIG4DFeUBRDXdBccOH3HGBZFPd8QwcUtxKmb7ohZPijqzQ6hA5QTngZq4MLeEr9ANTKaaCa5sKUXxkyR9JgqJ7FnbvF+hAQoOOaYdvuYJSy5iESABL8foVfvnmPw05dnTQ+mB8UHGv5+BgU+Bm7JZWydGoZKHtlynOzCqGDC/i1GulDRsbKRQN8d9RqsgW0Lwet/ZG4xCWRA9ugZNx7dUqeDFqh2DILOfzjM4EbQFLD+de2g7fMB+f2fcmERnNdtFr22XPqVyJ8MysHMkQH0PnqpN99ike0bPFhQR/JqR316ZFNwE21v5dYvF4ASevcv1/ErbkDSiR5ZlAcKkqF/Dppl2+AsYgnSfScTi+9TLLNqkoQx5ERQIN3a7v1BxR87rh1tUMwogi2Wa79mDhKy6bgDk3Zlrm6gHUCKszzu6ac0VtDPmnudIJoevkTyiL5gpPyOq3ijS0nlEJ3uyHnSokJx21R+DMndF7IV0C+pvz8pILKJ6QbZCJe9/nBoXhsrtuY9LErO5KSRyreJl24jKpEGLctwmuKH4cyLgkrL4e55MrGJybIWVuO0Nk5Ce4P5F6C8XJxg45FOzZRDVGSMWFlpc7+bI7au8S5tSucuS8enKLDlXPSB79SC6cmUGVjFO4j/oLD7MJdN/4VTEtZDfw7fEP/p8fdYQF9PYaxHQG63sM38smhXYilrAMVp+rwzPcOTx2HoaQibSaLJPnh4P3qqjN8Z/1Soslh7m7dGUNvC6PqQyOYUbiz+7VRUHDyrBLpoC2vY6yWisp1K1NHKmKzcjQM7pBH9YUoz3LvhyE26f3pY0oUpyo32KOu+ONOTCOoH4sE7XHozzk9K9mn3Ly2PC5DBg5oETvddVAgspKtgNuAA6fi60nB838HApfOYjk8FFkGd3cskF9t3HEaBGwFMO4qTPz8LiG9CD66JjTWNm2wUjvKOV+3eQa163TePor7A8yqlSWtF397ulaJX451fcHPsO/iF6qjKXifmU+YMzz5k/bFdcOKb1m1ESJ5Qirdh+GtN9tceEQfXC3X/Bu+Hl4TI2Cx6YyC1OLrvoLBmtoeP9xhioY/2TgYIZEMbM8w+FjaeuLqAC12YCoDMzXV0h2LwBgpocYg/73jP8PpGUpTiVWJCwwTLRoGrCFaDeQzGcJOh7gi1A5wma1dYMuYkdmuBMjD99U2PKYCI9yiAYaXk/MMdiaTJ4kd9ysFOeVgIWUam2mA9S7eQiTAFms0A/rCYTcpMHRJ/lyDHoQ0uCF3rJ83O6rDDCitbubXoNh3GrQxdTKFCjv8G1oVCxkxR+gDn/YljBkhdLwC89faTMOtxFuEn1Zb4m+NKl7GS9XQ/cW2ZxBhflsfaN1vN6REiO2F3WBfRPRAOvNMqyJuJ19182fe7fTGA1J9oRAFD4mlvtPjifAMG6/ctahyHD1/wOANCkDvSIk2+TmLAYH1Bg90/eZpfYczlkYZAAUeNMDOwATyFaHCysiYPsUBRbFlE7xanVadkaEb1AllzuOcF69YL2Dd8yU5Gvnu0/CW2pryHNaaav+05MZ+4qdAuOZsNaizsA38fWxbxnAdRzSQdKypWLtqhi0lt0sKP/+0CqYqWb7cpw5V39xSBN0aHv64k2D/VSkSkPVhXPZJUrVw6PCbUwX96yb3YHJYQxfOT9oATJxuvoWFkR6UmY9bLouzoyMvNAUXJoJAi5KgmUVoyzf6EBw+FYGikFaArH1yAzfCYZOHFP0nplaFmG5omslUgPmRv4HKTJId3pVhirGyeKBcTAjp0Qc3nT8TkEUyLzYxDfMVWLzTB5NAXwscLE2oC9DCNCLQ7nutJip0k7owJqAinmVzxJNMELzlyAK3Y+Zp6rYiWGSUQ8CSkVncgSMQHkt/4brSXAL26vy4rh5GZIcWTKGBPjwnkwJAFxQrVPZzyvroKgO//7yHLMW3cPoZux/AxbOX4cY+SWSa4wKMFJ8=",
        "__VIEWSTATEGENERATOR": "DC33F77C",
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": "4w09XwbAeSVbsDS3sl+33Pr8m6uc4hBNiYPHUTiac28QMAZdRSjytJOKPAToxplP+Ulicjw+nkRA+2pYgFgN7AsyYMbVEbg9kXuvwtTYNs7SP1luKPIrLgX1WuopBFT1zZ1pfJD6o9IkU7l8mZsz0IaTicM=",
        "TextBox1": "1",
        "TextBox2": "",
        "GridView1$ctl06$txtNewPageIndex": str(page)
    }

    res = s.post(aurl,data=form ,headers=header ,verify = False)

    # print(res.text)
    res_soup = BeautifulSoup(res.text, "html.parser")
    datalist = res_soup.find_all("span", {"id": re.compile("GridView1_ctl.*?_Label.*")})
    
    if not datalist:
        raise BaseException.APIException(msg='没有数据', error_code=30007)

    maxpage = res_soup.find("span", {"id": "GridView1_ctl06_lblPageCount"}).string

    arr = []
    item = {}
    keys = ["title", "speaker", "date", "loc", "content"]

    for i,val in enumerate(datalist):
        t = i%5
        q = val.contents
        w = ""
        for m in q:
            if type(m) == element.NavigableString:
                w = w + str(m)
        item[keys[t]] = w if keys[t]=="title" else "".join(w.split())
        if t == 4:
            arr.append(item)
            item = {}


    out = {}
    out["hasNext"] = 1 if int(maxpage)>int(page) else 0
    out["data"] = arr

    # print(json.dumps(out, ensure_ascii=False))
    return out

def school_tc_code(session, ip):

    # return {
    #     'msg': 'error',
    #     'captcha': False,
    #     'captchaHtml': False
    # }
    
    # 更新session
    s = requests.session()
    s.cookies.update({
        'language' : 'zh_CN',
        'sms_timeout' : '0'
    })
    if session:
        try:
            s.cookies.update(json.loads(session))
        except:
            pass
    s.cookies.update(get_vpnCookies())
    
    # print(s.cookies.get_dict())

    mobile_header = dict(mobile_h)
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    tc_code_url = base_url + "http/218.196.240.21/tycsweb/dimage.aspx"  
    code_img = s.get(tc_code_url, headers={
        'Host': 'webvpn.hpu.edu.cn',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        'sec-ch-ua-mobile': '?0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        # 'Cookie': 'ASP.NET_SessionId=g51my1n2wio2qv45n2qv5vfv; _gscu_1470794712=04212340zrx53y73; _gscbrs_1470794712=1; PHPSESSID=ST-601992-rXvl7NMkxqJZVnIFuq9l-uiahpueducn; huaucookie=1630253924',

    }) #, headers = mobile_header)
    # print(tc_code_url)
    print(code_img.text)
    # print(code_img.cookies.get_dict())
    if code_img.status_code != 200:
        raise BaseException.APIException(msg='登录超时，请重新登录', error_code=30002)

    base64_data = base64.b64encode(code_img.content)
    b64 = base64_data.decode()

    print("data:image/jpeg;base64,%s"%b64)
    return {
        'msg': 'success',
        'captcha': "data:image/jpeg;base64,%s"%b64,
        'captchaHtml': f"<img src='data:image/jpeg;base64,{b64}'></img>",
        'session': parse.quote(json.dumps(s.cookies.get_dict(), ensure_ascii=False))
    }


def school_tc_grade(session, usernum, userpwd, captcha, ip):

    def encrpthex2b64(password, public_key):
        rsakey = RSA.importKey(public_key)
        cipher = Cipher_pksc1_v1_5.new(rsakey)
        cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
        return cipher_text.decode()

    # 更新session
    s = requests.session()
    if session:
        s.cookies.update(json.loads(session))
    s.cookies.update(get_vpnCookies())

    mobile_header = dict(mobile_h)
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    tc_indexUrl = base_url + "http/218.196.240.21:80/tycsweb/index.aspx"
    index_res = s.get(tc_indexUrl, headers=mobile_header, verify = False)
    # print(index_res.text)
    ir_soup = BeautifulSoup(index_res.text, "html.parser")
    v1 = ir_soup.find(id="__EVENTTARGET").get("value")
    v2 = ir_soup.find(id="__EVENTARGUMENT").get("value")
    v3 = ir_soup.find(id="__VIEWSTATE").get("value")
    v4 = ir_soup.find(id="__VIEWSTATEGENERATOR").get("value")
    v5 = ir_soup.find(id="__EVENTVALIDATION").get("value")

    publicK_url = base_url + "http/218.196.240.21:80/tycsweb/GetPublicKey.ashx?op=get"
    pk_res = s.get(publicK_url, headers=mobile_header, verify = False)
    pk_res = json.loads(pk_res.text)
    # print(pk_res)
    if not pk_res['state']:
        raise BaseException.APIException(msg='访问失败，请尝试连接校园网浏览器后访问: http://218.196.240.21 进行查询', error_code=30005)

    public_key = '-----BEGIN PUBLIC KEY-----\n' + pk_res['msg'] + '\n-----END PUBLIC KEY-----'
    seed = pk_res['seed']
    usernum = encrpthex2b64(seed+usernum, public_key)
    userpwd = encrpthex2b64(seed+userpwd, public_key)

    payload = {
        "__EVENTTARGET": v1,
        "__EVENTARGUMENT": v2,
        "__VIEWSTATE": v3,
        "__VIEWSTATEGENERATOR": v4,
        "__EVENTVALIDATION": v5,
        "TextBox1": usernum,
        "TextBox2": userpwd,
        "TextBox3": captcha,
        "RadioButtonList1": "2",
        "Button1": "登录"
    }
    # print(payload)

    tc_url= base_url + "http/218.196.240.21:80/tycsweb/index.aspx"
    tc_page = s.post(tc_url, data=payload, verify = False)

    print(tc_page.text)
    if "运行时错误" in tc_page.text:
        raise BaseException.APIException(msg='校外访问关闭，查询请连接校园网后访问: http://218.196.240.21', error_code=30005)

    if "登录" in tc_page.text:
        errortip = BeautifulSoup(tc_page.text, "html.parser").find(attrs = {'type':'submit', 'name':'Button1'}).parent.get_text().split()[0]
        raise BaseException.APIException(msg=errortip, error_code=30006)

    tccj_url = base_url + "http/218.196.240.21/tycsweb/emyscore.aspx"
    tccj_p = s.get(tccj_url)

    tccj_soup = BeautifulSoup(tccj_p.text, "html.parser")
    tar_stunum = re.findall("学号：(.*)?</td>", tccj_p.text)[0].split()[0]
    nameurl = base_url + "http/218.196.240.21/root/fmleft1.aspx"
    tar_name = BeautifulSoup(s.get(nameurl, headers = mobile_header).text, "html.parser").find(id="Label1").string

    want_table = tccj_soup.find_all(class_="score-table")
    tds = BeautifulSoup(str(want_table), "html.parser").find_all("td")

    out = {}
    all_data = []
    # print(tds)
    box = []

    for td in tds:
        s = td.get_text()
        box.append(s)
        if "总分" in s:
            all_data.append(box)
            box = []

    out["name"] = tar_name
    out["stunum"] = tar_stunum
    out["data"] = all_data

    # print(json.dumps(out, ensure_ascii=False))
    return out 





