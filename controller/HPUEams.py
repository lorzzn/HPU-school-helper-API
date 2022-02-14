
# import fixpath
import pymysql
from urllib import parse
from flask import jsonify
from controller.confutil import *
from controller.common import *
from exception import BaseException


eams_base_url = "http://zhjw.hpu.edu.cn"
# eams_base_url = "http://218.196.248.100"

# get_vpnCookies()

eams_base_url = "http://zhjw.hpu.edu.cn"
# eams_base_url = "http://218.196.248.100"

# 获取教务session
def get_session(ip):
    # 登录教务
    login_url = f"{eams_base_url}/eams/loginExt.action"
    # 获取验证码
    captcha_url = f"{eams_base_url}/eams/captcha/image.action" # ?d="+str(round(time.time() * 1000))

    header = dict(req_header)

    # 链接教务官网
    header['X-Forwarded-For'] = ip
    # print(header)

    s = requests.session()
    s.cookies.update({
        'SVRNAME': 'xk1, xk2'
    })
    # print((parse.unquote(coo)))
    s.cookies.update(get_vpnCookies())

    # s.cookies.clear()
    # print(login_url)
    getSession = s.get(login_url, headers = header)
    # time.sleep(.5)
    getCaptcha = s.get(captcha_url, headers = header)

    # 处理数据
    login_soup = BeautifulSoup(getSession.text, 'html.parser')
    titles = login_soup.select("body script")

    # 获取sha1头和eas头
    print(getSession.text)
    sha1Header = re.findall('SHA1\(\'(.*?)\'', str(titles[0]))[0]
    aesHeader = re.findall('encrypt\(username,\'(.*)\'\)',str(titles[0]))[0]

    # 获取session
    d_session = json.dumps(s.cookies.get_dict()) # session

    # 验证码base64
    base64_data = base64.b64encode(getCaptcha.content)
    b64 = 'data:image/jpeg;base64,' + base64_data.decode()

    return {
        'content': parse.quote(d_session),
        'sha1H': sha1Header,
        'aesH': aesHeader,
        'captcha': b64,
        'captchaHtml': f"<img src='{b64}'></img>"
    }

# 登录教务
def login_eams(ip, username, password, captcha, session, sha1H, aesH):
    # 登录教务
    login_url = f"{eams_base_url}/eams/loginExt.action"
    # 验证码验证
    check_code_url = f"{eams_base_url}/eams/loginExt!getCodeFlag.action"

    header = dict(req_header)

    # 链接教务官网
    header['X-Forwarded-For'] = ip
    # 生成加密账号
    f1 = open("./controller/jsLib/aes.min.js")
    js1 = f1.read()
    f1.close()
    jstext = js1 + """
    function encrypt(content, key){
        var sKey = AesJS.enc.Utf8.parse(key);
        var sContent = AesJS.enc.Utf8.parse(content);
        var encrypted = AesJS.AES.encrypt(sContent, sKey, 
            {
                mode:AesJS.mode.ECB,
                padding: AesJS.pad.Pkcs7
            }
        );
        return encrypted.toString();
    }
    """ + f"encrypt('{username}', '{aesH}')"
    username = js2py.eval_js(jstext)

    # 生成密码
    genpass = sha1H + password
    sha = hashlib.sha1(genpass.encode('utf-8'))
    encrypts = sha.hexdigest()

    # 更新session
    # print(session)
    # s.cookies.update(json.loads(session)) # 读取
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取

    # 提交教务数据 
    payload = {
        'username':username,
        'password': encrypts,
        'captcha_response':captcha,
        'session_locale':'zh_CN'
    }

    check_res = s.post(check_code_url, {
        'captcha_response':captcha
    }, headers = header)
    cres = json.loads(check_res.text)
    if not cres["flag"]:
        return jsonify({
            'error_code': 10001,
            'msg': '验证码错误'
        })

    time.sleep(.5)
    login = s.post(login_url, data=payload, headers = header)
    # login = s.get(login_url, headers = req_header)
    login_soup = BeautifulSoup(login.text, 'html.parser')

    errorAct = login_soup.find(class_='actionError')
    if errorAct:
        return jsonify({
            'error_code': 10002,
            'msg': errorAct.get_text().strip()
        })
    
    session1 = json.dumps(s.cookies.get_dict(), ensure_ascii=False)
    return session1
    

# 教务学生资料信息
def eams_stu_info(session, ip):

    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    header = dict(req_header)
    header['X-Forwarded-For'] = ip


    # 学生信息页面
    std_detail_url = f"{eams_base_url}/eams/stdDetail.action"

    detail_act = s.post(std_detail_url, headers = header)
    # print(detail_act.text)
    # print(detail_act.history, detail_act.status_code)
    if len(detail_act.history) > 0:
        raise BaseException.APIException(msg='教务管理系统登录超时，请重新登录', error_code=10003)
 
    detail_soup = BeautifulSoup(detail_act.text, 'html.parser')
    item_title = list(detail_soup.find_all('td', class_='title'))

    stu_info = dict()
    for keyTag in item_title:
        if keyTag and keyTag.get_text().strip():
            key = keyTag.get_text().strip() #.replace('：','')
            valTag = keyTag.find_next_sibling('td', class_=None)
            stu_info[key] = valTag.get_text() if valTag else ""

    return stu_info

# 教务学生课程表
def eams_stu_timetable(session=None, semesterId=62, ip=None):
    
    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    header = dict(req_header)
    header['X-Forwarded-For'] = ip


    # 课程表页面
    timetable_url_f = f"{eams_base_url}/eams/courseTableForStd.action"
    timetable_url = f"{eams_base_url}/eams/courseTableForStd!courseTable.action"

    def isContinuationIntegerArray(array:list):
        array.sort()
        a = len(array)
        if array[-1]-array[0] == a-1: return True
        else: return False

    def findCanMergeCousre(array:list, item):
        if len(array)==0: return False
        for i,elem in enumerate(array):
            elemCopy = dict(elem)
            itemCopy = dict(item)
            if elemCopy['weekday'] != itemCopy['weekday']: continue
            tArray = elemCopy['sections'] + itemCopy['sections']
            tArray.sort()
            elemCopy.pop('weekday')
            elemCopy.pop('sections')
            elemCopy.pop('length')
            itemCopy.pop('weekday')
            itemCopy.pop('sections')
            itemCopy.pop('length')
            if itemCopy == elemCopy and isContinuationIntegerArray(tArray): return i
        return False

    timetable_page = s.post(timetable_url_f, headers = header)
    # 获取学生唯一课程表id
    get_ids = re.findall('"ids","(.*?)"', timetable_page.text)[0]
    #print('ids= '+get_ids)
    ttpayload = {
        'ignoreHead':'1',
        'setting.kind':'std',
        'startWeek':'',
        'project.id':'1',
        'semester.id':semesterId,
        'ids':get_ids
        }
    time.sleep(0.5)
    timetable_result = s.post(timetable_url, data = ttpayload)
    # print(timetable_result.text)
    t_res = BeautifulSoup(timetable_result.text,'html.parser')
    get_script = t_res.find_all('script')
    res_script = get_script[19].string


    # json化数据
    with open('./controller/jsLib/TaskActivity.js',encoding='utf8') as f1:
        js1 = f1.read()
    with open('./controller/jsLib/underscore.min.js',encoding='utf8') as f2:
        js2 = f2.read()
    sumjs = ('function getdata(){'
        + js1
        + js2
        + res_script
        + 'return JSON.stringify(table0);}'
    )
    raw = js2py.eval_js(sumjs+'\nvar res = getdata()')
    data1 = json.loads(raw)
    data = data1['activities']
    sl = int(len(data)/7)

    # 处理数据
    cdata = []
    for i in range(0, 7):
        for j in range(0, sl):
            ix = 10*i+j
            if not data[ix]: continue
            for item in data[ix]:
                item['weekday'] = i+1
                item['length'] = 1
                item['sections'] = [j+1]
                mi = findCanMergeCousre(cdata,item)
                if mi is False:
                    cdata.append(item)
                else:
                    cdata[mi]['sections'] += item['sections']
                    cdata[mi]['length'] += 1
    res_data = []
    for obj in cdata:
        res_data.append({
            'course': obj['courseName'],
            'course_id': obj['courseId'],
            'teacher_id': obj['teacherId'],
            'teacher': obj['teacherName'],
            'weekday': obj['weekday'],
            'sections': ",".join([str(t) for t in obj['sections']]),
            'length': obj['length'],
            'room_id': obj['roomId'],
            'loc': obj['roomName'],
            'active': ",".join([str(e) for e in [q for q,w in enumerate(obj['vaildWeeks']) if w=="1"]]),
            'vaildWeeks': obj['vaildWeeks'],
            'assistant': obj['assistantName'],
            'task_id': obj['taskId'],
            'remark': obj['remark'],
            'schGroupNo': obj['schGroupNo'],
            'experiItemName': obj['experiItemName']
        })
        
    res_data = 'empty' if len(res_data) == 0 else res_data
    # print(res_data)
    return res_data

# 教务学生成绩
def eams_stu_grade(session, stu_info, ip):

    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    header = dict(req_header)
    header['X-Forwarded-For'] = ip

    # 教务成绩页面
    grade_url = f"{eams_base_url}/eams/teach/grade/course/person!historyCourseGrade.action?projectType=MAJOR"
    
    grade_result = s.post(grade_url, headers=header)
    grade_soup = BeautifulSoup(grade_result.text, 'html.parser')
    tbodys = grade_soup.find_all("tbody")
    # gpa_detail = tbodys[0]

    tgpa = tbodys[0].find_all("tr")[:-2]

    gpa_data = []
    gra_data = []

    gpa_list = []
    for tr in tgpa:
        tds = tr.find_all("td")
        for td in tds:
            gpa_list.append(td.get_text())
    
    for t in range(0,int(len(gpa_list)/5)):
        gpa_data.append({
            'stu_num': stu_info['学号：'],
            'grade': stu_info['所在年级：'],
            'academy': stu_info['行政管理院系：'],
            'major': stu_info['专业：'],
            'class': stu_info['行政班级：'],
            'semester': str(gpa_list[5*t+0]).strip()+' '+ str(gpa_list[5*t+1]).strip(),
            'course': '学期平均绩点',
            'gpa': str(gpa_list[5*t+4]).strip(),
            'type': 2,
        })
        
    grade_detail = grade_soup.find_all('tbody')[1]
    grade_detail = list(grade_detail.find_all('td'))
    # print(grade_detail)
    grade_list = [i.get_text() if len(i)>0 else "无" for i in grade_detail]
    # print(grade_list)
    il = 10
    for i in range(0,int(len(grade_list)/il)):
        gra_data.append({
            'stu_num': stu_info['学号：'],
            'grade': stu_info['所在年级：'],
            'academy': stu_info['行政管理院系：'],
            'major': stu_info['专业：'],
            'class': stu_info['行政班级：'],
            'semester': str(grade_list[il*i+0]).strip(),
            'course_code': str(grade_list[il*i+1]).strip(),
            'course_num': str(grade_list[il*i+2]).strip(),
            'course': str(grade_list[il*i+3]).strip(),
            'course_type': str(grade_list[il*i+4]).strip()+"（"+str(grade_list[il*i+5]).strip()+"）",
            'credit': str(grade_list[il*i+6]).strip(),
            'overall_mark': str(grade_list[il*i+7]).strip(),
            'final_mark': str(grade_list[il*i+8]).strip(),
            'grade_point': str(grade_list[il*i+9]).strip(),
            'type': 1
        })

    return gpa_data + gra_data
    # {
    #     'gpa_data': gpa_data,
    #     'grade_data': gra_data
    # }    

# 绑定教务
def bind_eams(session=None, btype=None, semesterId=62, ip=None):
    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    
    # 学生信息、成绩、课程表
    if btype == '0':
        res = dict()
        res['stu_info'] = eams_stu_info(session, ip)
        res['stu_timetable'] = eams_stu_timetable(session, semesterId, ip)
        res['stu_score'] = eams_stu_grade(session, res['stu_info'], ip)

        return res

    # 课程表
    if btype == '1':
        res = dict()
        res['stu_info'] = {}
        res['stu_timetable'] = eams_stu_timetable(session, semesterId, ip)
        res['stu_score'] = {}

        return res

    # 成绩
    if btype == '2':
        res = dict()
        res['stu_info'] = {}
        res['stu_timetable'] = {}
        res['stu_score'] = eams_stu_grade(session, eams_stu_info(session, ip), ip)

        return res
    
    else:
        res = dict()
        res['stu_info'] = {}
        res['stu_timetable'] = {}
        res['stu_score'] = {}
    
        return res

# 获取学期列表
def eams_semesters(session, ip):
    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    header = dict(req_header)
    header['X-Forwarded-For'] = ip

    s.get(f"{eams_base_url}/eams/dataQuery.action", headers= header)
    page = s.post(f"{eams_base_url}/eams/dataQuery.action", data={
        'tagId': 'semesterBar20826294511Semester',
        'dataType': 'semesterCalendar',
        'value': '62',
        'empty': False
    }, headers= header)

    if "账号密码登录" in page.text:
        raise BaseException.APIException(msg='教务管理系统登录超时，请重新登录', error_code=10003)

    
    # psoup = BeautifulSoup(page.text, 'html.parser')
    # f_data = psoup.get_text()
    # print(page.text)
    f_data = page.text
    data = re.sub(r'(?<={|,)(\w+?)(?=:)', r'"\1"', f_data)
    data = json.loads(data)['semesters']

    result = list()
    for key in data:
        for item in data[key]:
            result.append({
                'school_year': item['schoolYear'],
                'name': item['name'],
                'semester_id': item['id']
            })
    return result


# 教务-空教室教学楼
def eams_freeroom_buildings(session):
    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    s.cookies.update({
        'SVRNAME': 'xk1, xk2'
    })
    s.cookies.update(get_vpnCookies())

    

    header = dict(req_header)
    # print(header)

    # 空教室查询页面
    freeroom_url = f"{eams_base_url}/eams/classroom/apply/free.action"

    s.get(f"{eams_base_url}/eams/classroom/apply/std-activity.action", headers= header)
    # print('1')
    time.sleep(.5)
    page = s.get(freeroom_url, headers= header)
    # print('2')

    print(page.text)

    if "账号密码登录" in page.text:
        raise BaseException.APIException(msg='教务管理系统登录超时，请重新登录', error_code=10003)

    psoup = BeautifulSoup(page.text, "html.parser")
    options = BeautifulSoup(str(psoup.find("select", id="building")), "html.parser").find_all("option")
    # print(options)

    data = []
    for o in options:
        if o.get("value") == "":
            continue
        # print("%s %s"%(o.get("value"), o.get("title")))
        d = {}
        d["value"] = o.get("value")
        d["title"] = o.get("title")
        data.append(d)

    # print(json.dumps(data, ensure_ascii=False))
    # print(data)
    return data if data else False

# 教务-查询空教室
def eams_freeroom_search(session, buildingId, dateBegin, dateEnd, section, mode, ip):

    # 更新session
    s = requests.session()
    if session: s.cookies.update(json.loads(session)) # 读取
    s.cookies.update(get_vpnCookies())

    a = buildingId 
    b = dateBegin  
    c = dateEnd    
    d = section    
    e = mode
    f = ip

    def sectionFree(buildingId, dateBegin, dateEnd, section, mode):

        result = s.post(f"{eams_base_url}/eams/classroom/apply/free!search.action", 
        data={
            "classroom.building.id":buildingId,              # 教学楼id
            "cycleTime.cycleCount":"1",                      # 时间周期
            "cycleTime.cycleType":"1",                       # 周期类型（1：天，2：周）
            "cycleTime.dateBegin":dateBegin,                 # 起始空闲日期
            "cycleTime.dateEnd":dateEnd,                     # 结束空闲日期
            "roomApplyTimeType":"0",                         # 空闲时间单位（0：小节，1：时间）
            "timeBegin":str(section).split("-")[0],          # 起始空闲小节/时间
            "timeEnd":str(section).split("-")[1],            # 结束空闲小节/时间
            "pageNo":"1",                                    # 当前页码
            "pageSize":"1000",                               # 一页显示的条目数
            "orderBy":"classroom.name asc"                   # 排序方式（classroom.name asc：名称升序）
        }, headers=req_header)
        # print(result.text)
        if "账号密码登录" in result.text:
            raise BaseException.APIException(msg='教务管理系统登录超时，请重新登录', error_code=10003)
        if "过快点击" in result.text:       # 请不要过快点击
            raise BaseException.APIException(msg='请不要过快点击', error_code=10004)
        if "返回前页" in result.text:
            errMsg = re.findall("<span>(.*)</span>", result.text)[0]
            raise BaseException.APIException(msg=errMsg, error_code=10005)

        rsoup = BeautifulSoup(result.text, "html.parser")
        dataTable = rsoup.find("tbody", id=re.compile("grid.*data"))
        # print(dataTable)

        data = []
        trs = dataTable.find_all("tr")
        for tr in trs:
            tds = tr.find_all("td")
            if not tds:
                return []
            d = {}
            d["num"] = tds[0].string.strip() if tds[0].string else ""
            # d["startSection"] = str(section).split("-")[0]
            # d["endSection"] = str(section).split("-")[1]
            d["name"] = tds[1].string.strip() if tds[1].string else ""
            if mode == '1':
                d["building"] = tds[2].string.strip() if tds[2].string else ""
                d["campus"] = tds[3].string.strip() if tds[3].string else ""
                d["type"] = tds[4].string.strip() if tds[4].string else ""
                d["seats"] = tds[5].string.strip() if tds[5].string else ""
            data.append(d)

        # print(json.dumps(data, ensure_ascii=False))
        return data

    def autoMode(e):
        result = []
        for i in range(1,11):
            section = str(i)+"-"+str(i)
            r = sectionFree(a, b, c, section, e)
            result.append({
                'startSection':str(i),
                'endSection':str(i),
                'roomList':r
            })
            time.sleep(.5)
        return result

    def manualMode(section, e):
        result= []
        r = sectionFree(a, b, c, section, e)
        result.append({
            'startSection':section.split("-")[0],
            'endSection':section.split("-")[1],
            'roomList':r
        })
        return result

    if d == "0-0" or d == "0":
        res = autoMode(e)
    else:
        res = manualMode(d, e)

    # print(json.dumps(res, ensure_ascii=False))
    return res





