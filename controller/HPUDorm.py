

import datetime
from urllib import parse
from flask import jsonify
from controller.confutil import *
from exception import BaseException


def dorm_elec_search(lou=None, ceng=None, room=None, ip='47.103.223.186'):
    
    s = requests.session()

    url = "http://183.169.255.4:8080/Default.aspx"
    r_url = "http://183.169.255.4:8080/usedRecord.aspx"

    page1 = s.get(url).text
    psoup1 = BeautifulSoup(page1, 'html.parser')
    v1 = psoup1.find(id="__VIEWSTATE")
    vs1 = v1.get("value")
    sel1 = psoup1.find_all("select")[0]
    opts = sel1.find_all("option")
    q = []
    for o in opts:
        p = {}
        p["label"] = o.string
        p["value"] = o.get("value")
        if p["label"] and p["value"]:
            q.append(p)
    # print(json.dumps(q[1:], ensure_ascii=False))
    # lou = input("请选择宿舍楼：")
    if not lou:
        # sys.exit(0)
        return jsonify({
            'msg': 'success',
            'data': q
        })
    pl1 = {
        "__EVENTTARGET": "drlouming",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": vs1,
        "drlouming": lou,
        "ablou": "",
        "drceng": ""
    }
    page2 = s.post(url, data = pl1).text
    psoup2 = BeautifulSoup(page2, 'html.parser')
    v2 = psoup2.find(id="__VIEWSTATE")
    vs2 = v2.get("value")
    sel2 = psoup2.find_all("select")[1]
    opts = sel2.find_all("option")
    q = []
    for o in opts:
        p = {}
        p["label"] = o.string
        p["value"] = o.get("value")
        if p["label"] and p["value"]:
            q.append(p)
    # print(json.dumps(q[1:], ensure_ascii=False))
    # ceng = input("请选择楼层：")
    if not ceng:
        # sys.exit(0)
        return jsonify({
            'msg': 'success',
            'data': q
        })
    pl2 = {
        "__EVENTTARGET": "ablou",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": vs2,
        "drlouming": lou,
        "ablou": ceng,
        "drceng": ""
    }
    page3 = s.post(url, data=pl2).text
    psoup3 = BeautifulSoup(page3, 'html.parser')
    v3 = psoup3.find(id="__VIEWSTATE")
    vs3 = v3.get("value")
    sel3 = psoup3.find_all("select")[2]
    opts = sel3.find_all("option")
    q = []
    for o in opts:
        p = {}
        p["label"] = o.string
        p["value"] = o.get("value")
        if p["label"] and p["value"]:
            q.append(p)
    # print(json.dumps(q[1:], ensure_ascii=False))
    # room = input("请选择房间：")
    if not room:
        # sys.exit(0)
        return jsonify({
            'msg': 'success',
            'data': q
        })
    pl3 = {
        "__EVENTTARGET": "drceng",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": vs3,
        "drlouming": lou,
        "ablou": ceng,
        "drceng": room,
        "radio": "usedR",
        "ImageButton1.x": "70",
        "ImageButton1.y": "21"
    }
    page4 = s.post(url, data=pl3).text
    psoup4 = BeautifulSoup(page4, 'html.parser')
    vs4 = psoup4.find(id="__VIEWSTATE").get("value")
    ev = psoup4.find(id="__EVENTVALIDATION").get("value")

    enddate = datetime.datetime.now().strftime("%Y-%m-%d")
    startdate = (datetime.datetime.now()+datetime.timedelta(days=-10)).strftime("%Y-%m-%d")
    # print(startdate)
    # print(enddate)
    pl4 = {
        "__VIEWSTATE": vs4,
        "__EVENTVALIDATION": ev,
        "txtstart": startdate,
        "txtend": enddate,
        "btnser": "查询"
    }
    page5 = s.post(r_url, data=pl4).text
    psoup5 = BeautifulSoup(page5, 'html.parser')
    numo = psoup5.find_all(class_="number orange")
    sres = psoup5.find_all(class_="contentLine")

    # print(numo)
    # print(sres)

    a = {}
    a["buyR"] = numo[0].string
    a["graR"] = numo[1].string
    a["sumR"] = numo[2].string
    b = []
    for item in sres:
        c = {}
        trs = item.find_all("td")
        c["date"] = trs[0].string
        c["name"] = trs[1].string
        c["usel"] = trs[2].string
        b.append(c)

    output = {}
    output["now"] = a
    output["recent"] = b
    # output = json.dumps(output, ensure_ascii=False)
    # print(output)
    return jsonify({
            'msg': 'success',
            'data': output
        })













