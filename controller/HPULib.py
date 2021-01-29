

from urllib import parse
from flask import jsonify
from controller.common import *
from controller.confutil import *
from exception import BaseException


def lib_session(ip='47.103.223.186'):

    s = requests.session()

    code_url = 'https://mfindhpu.libsp.com/oga/verifycode/img?'

    header = {
        'Host': 'mfindhpu.libsp.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7'
    }

    # s.get('https://mfindhpu.libsp.com/#/login', verify=False)
    code_res = s.get(code_url, headers=header, verify=False)
    res = json.loads(code_res.text.replace('\\n',''))
    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    # print(code_res.text)
    res['session'] = parse.quote(json.dumps(s.cookies.get_dict(), ensure_ascii=False))
    res['captchaHtml'] = f"<img src='{res['data']['verifyCode']}'></img>"

    return jsonify(res)

def lib_login(session, username, password, captcha, codeKey, ip):

    s = requests.session()
    s.cookies.update(json.loads(session))

    payload = {
        'username': username, 
        'password': password, 
        'verifyCode': captcha, 
        'mappingPath': '', 
        'nextpath': '/Home', 
        'codeKey': codeKey, 
        'uid': ''
    }

    header = {
        'Host': 'mfindhpu.libsp.com',
        'Connection': 'keep-alive',
        'Content-Length': '157',
        'Accept': 'application/json, text/plain, */*',
        'mappingPath': '',
        'groupCode': '200090',
        'null': 'null',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://mfindhpu.libsp.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://mfindhpu.libsp.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'

    }
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    res = s.post('https://mfindhpu.libsp.com/oga/login',
        data=json.dumps(payload),
        headers=header,
        verify=False
    )
    # print(res.text)
    
    res = json.loads(res.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    # loan_page = s.get('https://mfindhpu.libsp.com/find/loanInfo/loanHistoryList', headers = header)
    # print(loan_page.text)

    session_d = s.cookies.get_dict()
    session_d.update(res['data'])

    return jsonify({
        'msg': 'success',
        'data': parse.quote(json.dumps(session_d, ensure_ascii=False))
    })


def lib_loan_list(session, ip):

    header = {
        'Host': 'mfindhpu.libsp.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    
    s = requests.session()
    s_d = json.loads(session)
    s.cookies.update(s_d)

    header['jwtOpacAuth'] = s_d['jwt']
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    loan_data = s.post(
        'https://mfindhpu.libsp.com/find/loanInfo/loanHistoryList',
        data=json.dumps({
            'page': 1,
            'rows': 20000
        }),
        headers=header, 
        verify=False
    )
    res = json.loads(loan_data.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    # print(loan_data.text)

    return jsonify({
        'msg': res['message'],
        'data': res['data']
    })


def lib_simple_search(keyword,page, ip):

    header = {
        'Host': 'mfindhpu.libsp.com',
        'Connection': 'keep-alive',
        'Content-Length': '522',
        'Accept': 'application/json, text/plain, */*',
        'mappingPath': '',
        'groupCode': '200090',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://mfindhpu.libsp.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://mfindhpu.libsp.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    s = requests.session()

    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    req_url = 'https://mfindhpu.libsp.com/find/unify/search'

    payload = {
        'docCode': [None], 
        'searchFieldContent': keyword, 
        'searchField': 'keyWord', 
        'matchMode': '2', 
        'resourceType': [], 
        'subject': [], 
        'discode1': [], 
        'publisher': [], 
        'locationId': [], 
        'collectionName': [], 
        'author': [], 
        'langCode': [], 
        'countryCode': [], 
        'publishBegin': None, 
        'publishEnd': None, 
        'coreInclude': [], 
        'ddType': [], 
        'verifyStatus': [], 
        'group': [], 
        'sortField': 'relevance', 
        'sortClause': 'asc', 
        'page': page, 
        'rows': 10, 
        'onlyOnShelf': None, 
        'campusId': [], 
        'curLocationId': [], 
        'eCollectionIds': [], 
        'kindNo': [], 
        'libCode': [], 
        'searchItems': None, 
        'searchFieldList': None
    }

    res = s.post(req_url, headers=header, data=json.dumps(payload), verify=False)

    res = json.loads(res.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    # print(res.text)
    return jsonify({
        'msg': res['message'],
        'data': res['data']
    })


def lib_book_detail(recordId, ip, jsonify_res=True):

    header = {
        'Host': 'mfindhpu.libsp.com',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'mappingPath': '',
        'groupCode': 'undefined',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://mfindhpu.libsp.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    s = requests.session()

    res = s.get(f'https://mfindhpu.libsp.com/find/searchResultDetail/getDetail?recordId={recordId}', headers=header, verify=False)

    res = json.loads(res.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    data = {
        'msg': res['message'],
        'data': res['data']
    }
    # print(res.text)
    return jsonify(data) if jsonify_res else data


def lib_book_collection(recordId, ip):
    
    header = {
        'Host': 'mfindhpu.libsp.com',
        'Connection': 'keep-alive',
        'Content-Length': '71',
        'Accept': 'application/json, text/plain, */*',
        'mappingPath': '',
        'groupCode': 'undefined',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.50',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://mfindhpu.libsp.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://mfindhpu.libsp.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    header['X-Forwarded-For'] = ip if ip else '47.103.223.186'

    s = requests.session()

    res = s.post('https://mfindhpu.libsp.com/find/physical/groupitems',
        data=json.dumps({
            'page': 1, 
            'rows': 20000, 
            'entrance': None, 
            'recordId': recordId, 
            'isUnify': True
        }),
        headers=header, 
        verify=False
    )

    res = json.loads(res.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    data = {
        'msg': res['message'],
        'data': res['data']
    }
    # print(res.text)
    return jsonify(data)


def lib_book_cover(recordId, raw=False, ip=None):

    detail = lib_book_detail(recordId=recordId, ip=ip, jsonify_res=False)

    s = requests.session()

    # print(detail)
    bookname = detail['data']['bean2List'][0]['fieldVal'].split('/')[0]
    bookisbn = detail['data']['bean2List'][2]['fieldVal'].split('/')[0]

    res = s.get(f'https://mfindhpu.libsp.com/find/book/getDuxiuImageUrl?title={bookname}&isbn={bookisbn}', verify=False)

    res = json.loads(res.text)

    if not res['success']:
        raise BaseException.APIException(msg=res['message'], error_code=res['errCode'])

    if raw:
        img_content = s.get(res['data'], verify=False).content
        img_content_b64 = encode_base64(img_content)
        return "data:image/jpg;base64,%s"%img_content_b64

    data = {
        'msg': res['message'],
        'data': res['data']
    }
    # print(res.text)
    return jsonify(data)








