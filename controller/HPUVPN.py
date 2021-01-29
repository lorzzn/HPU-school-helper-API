
import os
import img2pdf
import pypandoc
import subprocess
from bs4 import element
from PIL import Image
from urllib import parse
from flask import jsonify
from controller.confutil import *
from exception import BaseException
from controller.common import *


def login_hpu_vpn(jwzh, jwmm, ip):

    s = requests.session()

    baseurl = "https://vpn.hpu.edu.cn/por/login_psw.csp?encrypt=0"
    mobile_header = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"
    }
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    formData = {
        "svpn_name": jwzh,
        "svpn_password": jwmm
    }

    s.post(baseurl, data=formData, headers=mobile_header, verify = False, allow_redirects=False)
    cok = s.cookies.get_dict()

    if "ENABLE_RANDCODE" not in cok:
        raise BaseException.APIException(msg='密码错误', error_code=30001)

    s.get("https://vpn.hpu.edu.cn/web/1/http/0/218.196.240.155/swfweb/hpugg.aspx", headers= mobile_header, verify = False, allow_redirects=False)

    # print(json.dumps(s.cookies.get_dict(), ensure_ascii=False))
    session = json.dumps(s.cookies.get_dict(), ensure_ascii=False)

    return jsonify({
        'msg': 'success',
        'session': parse.quote(session)
    })


def school_ann(session, page, ip):
        
    aurl = "https://vpn.hpu.edu.cn/web/1/http/0/218.196.240.155:80/swfweb/hpugg.aspx"

    header = req_header
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    # 更新session
    s.cookies.update(json.loads(session)) # 读取

    # 请求页面
    res = s.get(aurl+"?page="+str(page),headers=header, verify = False)
    # print(res.text, res.status_code)
    if res.status_code != 200:
        raise BaseException.APIException(msg='登录超时，请重新登录', error_code=30002)

    res_soup = BeautifulSoup(res.text, "html.parser")
    maxpage = res_soup.find_all("span", {"id": "Label4"})[0].string
    annnum = res_soup.find_all("span", {"id": "Label1"})[0].string

    ahrefs = res_soup.find_all("a", {"href": re.compile("/web/.*?id=.*")})

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

    # print(json.dumps(out, ensure_ascii=False))
    return jsonify({
        'msg': 'success',
        'data': out
    })


def school_ann_download(session, ann_id):
    
    # requests.urllib3.disable_warnings()

    def mkdirW(path):
        isExis = os.path.exists(path)
        if not isExis:
            os.makedirs(path)

    aid = ann_id

    aurl = "https://vpn.hpu.edu.cn/web/1/http/2/218.196.240.155/swfweb/hpugm.aspx?id="+aid

    # 更新session
    s = requests.session()
    s.cookies.update(json.loads(session)) # 读取

    res = s.get(aurl, verify = False)

    if res.status_code != 200:
        raise BaseException.APIException(msg='获取公告内容失败', error_code=30003)

    fUrl = parse.unquote(res.url)
    fName = fUrl.split("/")[-1:][0]
    fType = fUrl.split(".")[-1:][0]

    rootdir = "./public/sources/anns/"
    tempdir = './public/sources/temp/'
    itemdir = rootdir + aid + "/"
    mkdirW(itemdir)

    file_base_url = "http://127.0.0.1/"

    if fType.lower() in ["doc","docx","xls","xlsx","ppt","pptx","pdf"]:
        with open(itemdir + fName, "wb") as f:
            f.write(res.content)
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })

    if fType.lower() in ["rtf"]:
        with open(itemdir + fName + ".doc", "wb") as f:
            f.write(res.content)
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })

    if fType.lower() in ["jpg","jpeg","gif","png"]:
        tempfile = tempdir+fName
        # print(tempfile)
        with open(tempfile, "wb") as d:
            d.write(res.content)
        with open(itemdir + fName + ".pdf", "wb") as f:
            i = Image.open(tempfile)
            i = i.convert("RGB")
            i.save(tempfile)
            f.write(img2pdf.convert(tempfile))
            os.remove(tempfile)
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })
    
    if fType.lower() in ["html", "htm"] and res.status_code == 200:
        pypandoc.convert_text(res.text, "docx", "html", outputfile=itemdir + "/公告内容.docx")
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })

    if fType.lower() in ["zip", "7z"]:
    # if fType.lower() in ["zip"]:
        tempfile = tempdir+aid+"."+fType
        with open(tempfile, "wb") as f:
            f.write(res.content)
        cmdw = "LANG='zh_CN.UTF-8' 7za e -aoa '{}' -o{}".format(tempfile, itemdir)
        # cmdw = "LANG='zh_CN.UTF-8' unzip -j '{}' -o -d {}".format(tempfile, rootdir+"/"+aid)
        # print(cmdw)
        subprocess.call(cmdw, shell=True)
        os.remove(tempfile)
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })

    if fType.lower() in ["rar"]:
        tempfile = tempdir+aid+"."+fType
        with open(tempfile, "wb") as f:
            f.write(res.content)
        cmdw = "LANG='zh_CN.UTF-8' unrar e -o+ '{}' {}".format(tempfile, itemdir)
        # print(cmdw)
        subprocess.call(cmdw, shell=True)
        os.remove(tempfile)
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })

    if fType.lower() in ["aspx"] and res.status_code == 200:
        # print(rootdir+aid+"/公告内容.docx")
        pypandoc.convert_text(res.text, "docx", "html", outputfile=itemdir + "/公告内容.docx")
        return jsonify({
            'msg': 'success',
            'data': [file_base_url + i for i in os.listdir(itemdir)]
        })


def school_lectures(session, page, ip):
    
    # 更新session
    s = requests.session()
    s.cookies.update(json.loads(session))

    aurl = "https://vpn.hpu.edu.cn/web/1/http/0/218.196.240.155:80/swfweb/hpugg.aspx"
    header = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0'
    }
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
    return jsonify({
        'msg': 'success',
        'data': out
    })


def school_tc_code(session, ip):
    
    # 更新session
    s = requests.session()
    s.cookies.update(json.loads(session))

    mobile_header = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"
    }
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    tc_code_url = "https://vpn.hpu.edu.cn/web/0/http/2/218.196.240.21/tycsweb/dimage.aspx"  
    code_img = s.get(tc_code_url, headers = mobile_header)

    # print(code_img.text)
    if code_img.status_code != 200:
        raise BaseException.APIException(msg='登录超时，请重新登录', error_code=30002)

    base64_data = base64.b64encode(code_img.content)
    b64 = base64_data.decode()

    # print("data:image/jpeg;base64,%s"%b64)
    return jsonify({
        'msg': 'success',
        'captcha': "data:image/jpeg;base64,%s"%b64,
        'captchaHtml': f"<img src='data:image/jpeg;base64,{b64}'></img>"
    })


def school_tc_grade(session, usernum, userpwd, captcha, ip):

    # 更新session
    s = requests.session()
    s.cookies.update(json.loads(session))

    mobile_header = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"
    }
    mobile_header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": "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",
        "__VIEWSTATEGENERATOR": "C0FF12A6",
        "__EVENTVALIDATION": "d99tH4eWTqHuAmg6Cke3uYUqXKzohb8rAcjAWFo6pGFfCtf+PW7uhVyjcxrnpxYyUNsRApWPhpqtJZSyBalm6IwSq2Z96yWaVyuSOgRhAOVoTrvfppTvT/kMHheylaHVhJC/XT3tlmO/h+HGQ3euC0N+/vSx6wOk6Md5ng==",
        "TextBox1": usernum,
        "TextBox2": userpwd,
        "TextBox3": captcha,
        "RadioButtonList1": "2",
        "Button1": "登录"
    }

    tc_url= "https://vpn.hpu.edu.cn/web/1/http/1/218.196.240.21:80/tycsweb/index.aspx"
    tc_page = s.post(tc_url, payload, verify = False)

    # print(tc_page.text)
    if "运行时错误" in tc_page.text:
        raise BaseException.APIException(msg='校外访问关闭，请链接校园网访问http://218.196.240.21查询', error_code=30005)

    if "登录" in tc_page.text:
        raise BaseException.APIException(msg='密码错误', error_code=30006)

    tccj_url = "https://vpn.hpu.edu.cn/web/1/http/2/218.196.240.21/tycsweb/emyscore.aspx"
    tccj_p = s.get(tccj_url)

    tccj_soup = BeautifulSoup(tccj_p.text, "html.parser")
    tar_stunum = re.findall("学号：(.*)?</td>", tccj_p.text)[0].split()[0]
    nameurl = "https://vpn.hpu.edu.cn/web/1/http/2/218.196.240.21/root/fmleft1.aspx"
    tar_name = BeautifulSoup(s.get(nameurl, headers = mobile_header).text, "html.parser").find(id="Label1").string

    want_table = tccj_soup.find(class_="score-table")
    tds = BeautifulSoup(str(want_table), "html.parser").find_all("td")

    out = {}
    all_data = []
    # print(tds)
    box = []

    for td in tds:
        s = td.string
        box.append(s)
        if "总分" in s:
            all_data.append(box)
            box = []

    out["name"] = tar_name
    out["stunum"] = tar_stunum
    out["data"] = all_data

    # print(json.dumps(out, ensure_ascii=False))
    return jsonify({
        'msg': 'success',
        'data': out
    })





