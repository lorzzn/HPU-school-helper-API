
from datetime import date
import logging
from urllib import parse
from flask import Flask, jsonify, request, json
from flask_caching import Cache
from validate import BaseValidate
from exception import BaseException
from controller import HPUEams, HPUZhhq, HPUVPN, HPUDorm, HPULib

app = Flask(__name__)
cache = Cache(config={
        'CACHE_TYPE' : 'filesystem', # 使用文件系统来存储缓存的值
        'CACHE_DIR' : './runtime/cache', # 文件目录
        'CACHE_DEFAULT_TIMEOUT' : 600 # 默认过期/超时时间，单位为秒
    })
cache.init_app(app)

@app.route('/')
def index():
    return 'Hello HPU_School_Helper_APIs!'

# 获取教务session
# 接收：ip
# 返回：session content, shaHeader, aesHeader, captcha
@app.route('/eams/session', methods=['POST'])
def EamsSession():
    BaseValidate.paramsExist(
        request.args.to_dict(), 
        ['ip']
    )
    data = HPUEams.get_session(
        request.args['ip']
    )
    return jsonify(data)

# 登录教务 (eams)
# 接收：ip, username, password, captcha, session, sha1H, aesH
# 返回：session content
@app.route('/eams/login', methods=['POST'])
def EamsLogin():
    BaseValidate.paramsExist(
        request.args.to_dict(), 
        ['ip', 'username', 'password', 'captcha', 'session', 'sha1H', 'aesH']
    )
    args = request.args
    data = HPUEams.login_eams(
        args['ip'],
        args['username'],
        args['password'],
        args['captcha'],
        args['session'],
        args['sha1H'],
        args['aesH']    
    )
    return jsonify({
        'msg': 'success',
        'session': parse.quote(data)
    })

# 绑定教务 （用户账户绑定、获取课程表、获取成绩）
# 接收：session (已成功登录教务的) , type, semesterId, ip
# 返回：stu_info, stu_timetable, stu_grade
@app.route('/eams/bind', methods=['POST'])
def EamsBind():
    BaseValidate.paramsExist(
        request.args.to_dict(), 
        ['session', 'type', 'semesterId', 'ip']
    )
    data = HPUEams.bind_eams(
        request.args['session'], 
        request.args['type'],
        request.args['semesterId'],
        request.args['ip']
    )
    return jsonify(data)


# 获取学期列表
# 接收: session, ip
# 返回: data
@app.route('/eams/semesters', methods=['POST', 'GET'])
def EamsSemesters():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'ip']
    )
    data = HPUEams.eams_semesters(
        request.args['session'],
        request.args['ip']
    )
    return  jsonify({
        'msg': 'success',
        'data': data
    })


# 获取空教室查询教学楼
# 接收：session
# 返回：data
@app.route('/eams/freeroom/buildings', methods=['POST'])
def EamsFreeroomBuildings():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session']
    )
    data = HPUEams.eams_freeroom_buildings(
        request.args['session']
    )
    return  jsonify({
        'msg': 'success',
        'data': data
    })

# 查询空教室
# 接受：             
#   buildingId        # buildingID(value);                                                  eg:1
#   dateBegin         # 开始日期;                                                           eg:2020-09-09        
#   dateEnd           # 结束日期;                                                           eg:2020-09-09
#   section           # 0:自动爬取第1至第10小节；1-10：对应小节;                              eg:0/1-2
#   mode              # 0:精简模式（只有教室名称）；1：详细模式（结果包括教室信息）;           eg:0/1
#   ip                # 客户端ip;                                                           eg:223.90.25.199    
#返回
@app.route('/eams/freeroom/search', methods=['POST'])
def EamsFreeroomSearch():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session','buildingId','dateBegin','dateEnd','section','mode', 'ip']
    )
    data = HPUEams.eams_freeroom_search(
        request.args['session'],
        request.args['buildingId'],
        request.args['dateBegin'],
        request.args['dateEnd'],
        request.args['section'],
        request.args['mode'],
        request.args['ip']
    )
    return  jsonify({
        'msg': 'success',
        'data': data
    })

# 获取校园保修session
# 接收：ip
# 返回：session, lt, execution, token, captcha, captchaHtml
@app.route('/zhhq/session', methods=['POST'])
def ZhhqSession():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['ip']
    )
    data = HPUZhhq.get_session(
        request.args['ip']
    )
    return jsonify(data)

# 登录校园报修
# 接收：username, password, session, lt, execution, token, captcha, ip
# 返回：academy, avatar, dorm, nickname, session
@app.route('/zhhq/login', methods=['POST'])
def ZhhqLogin():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['username', 'password', 'session', 'lt', 'execution', 'token', 'captcha', 'ip']
    )
    data = HPUZhhq.login_zhhq(
        request.args['session'],
        request.args['username'],
        request.args['password'],
        request.args['captcha'],
        request.args['lt'],
        request.args['execution'],
        request.args['token'],
        request.args['ip'],
    )
    return jsonify(data)

# 登录HPU校外访问VPN
# 接受：jwzh, jwmm, ip
# 返回：session
@app.route('/hpuvpn/login', methods=['POST'])
def HpuvpnLogin():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['jwzh', 'jwmm', 'ip']
    )
    data = HPUVPN.login_hpu_vpn(
        request.args['jwzh'],
        request.args['jwmm'],
        request.args['ip']
    )
    return  jsonify({
        'msg': 'success',
        'session': parse.quote(data)
    })

# 获取公告列表
# 接受：session, page, ip
# 返回：data
@app.route('/hpuvpn/school/ann', methods=['POST'])
def SchoolAnn():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'page', 'ip']
    )
    data = HPUVPN.school_ann(
        request.args['session'],
        request.args['page'],
        request.args['ip']
    )
    return jsonify({
        'msg': 'success',
        'data': data
    })

# 获取公告文件列表
# 接受：session, annid
# 返回：data
@app.route('/hpuvpn/school/ann/list', methods=['POST'])
def AnnList():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'annid']
    )
    data = HPUVPN.school_ann_download(
        request.args['session'],
        request.args['annid']
    )
    return jsonify(data)

# 获取讲座列表
# 接受：session, page, ip
# 返回：data
@app.route('/hpuvpn/school/lectures', methods=['POST'])
def SchoolLectures():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'page', 'ip']
    )
    data = HPUVPN.school_lectures(
        request.args['session'],
        request.args['page'],
        request.args['ip']
    )
    return jsonify({
        'msg': 'success',
        'data': data
    })


# 获取体测验证码
# 接受：session, ip
# 返回：captcha
@app.route('/hpuvpn/tc/code', methods=['POST'])
def TcCode():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'ip']
    )
    data = HPUVPN.school_tc_code(
        request.args['session'],
        request.args['ip']
    )
    return jsonify(data)

# 获取体测成绩
# 接受：session, usernum, userpwd, captcha, ip
# 返回：data
@app.route('/hpuvpn/tc/grade', methods=['POST'])
def TcGrade():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'usernum', 'userpwd', 'captcha', 'ip']
    )
    data = HPUVPN.school_tc_grade(
        request.args['session'],
        request.args['usernum'],
        request.args['userpwd'],
        request.args['captcha'],
        request.args['ip']
    )
    return jsonify({
        'msg': 'success',
        'data': data
    })

# 获取宿舍电费使用情况
# 接受：lou(可选), ceng(可选), room(可选)
# 返回：data
@app.route('/dorm/electricity', methods=['POST'])
def DormElectricity():
    args_d = request.args.to_dict()
    data = HPUDorm.dorm_elec_search(
        args_d['lou'] if 'lou' in args_d else None,
        args_d['ceng'] if 'ceng' in args_d else None,
        args_d['room'] if 'room' in args_d else None,
        args_d['ip'] if 'ip' in args_d else None
    )
    return jsonify({
        'msg': 'success',
        'data': data
    })

# 获取图书馆session
# 接收：ip
# 返回: session
@app.route('/lib/session', methods=['POST'])
def LibSession():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['ip']
    )
    data = HPULib.lib_session(
        request.args['ip']
    )
    return  jsonify(data)

# 登录图书馆
# 接收: session, username, password, captcha, codeKey, ip
# 返回: session 
@app.route('/lib/login', methods=['POST'])
def LibLogin():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'username', 'password', 'captcha', 'codeKey', 'ip']
    )
    data = HPULib.lib_login(
        request.args['session'],
        request.args['username'],
        request.args['password'],
        request.args['captcha'],
        request.args['codeKey'],
        request.args['ip'],
    )
    return jsonify({
        'msg': 'success',
        'data': parse.quote(json.dumps(data, ensure_ascii=False))
    })


# 获取图书馆借阅信息
# 接收: session
# 返回: data
@app.route('/lib/loanList', methods=['POST'])
def LibLoanList():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['session', 'ip']
    )
    data = HPULib.lib_loan_list(
        request.args['session'],
        request.args['ip']
    )
    return jsonify(data)


# 简单搜索馆藏
# 接收: keyword, page, ip
# 返回: data
@app.route('/lib/book/simpleSearch', methods=['POST'])
def BookSimpleSearch():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['keyword', 'page', 'ip']
    )
    data = HPULib.lib_simple_search(
        request.args['keyword'],
        request.args['page'],
        request.args['ip']
    )
    return jsonify(data)


# 图书馆图书详情
# 接收: recordId, ip
# 返回: data
@app.route('/lib/book/detail', methods=['GET', 'POST'])
def BookDetail():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['recordId', 'ip']
    )
    data = HPULib.lib_book_detail(
        request.args['recordId'],
        request.args['ip']
    )
    return jsonify(data)

# 图书馆图书封面
# 接收: recordId, ip
# 返回: data
@app.route('/lib/book/cover', methods=['GET', 'POST'])
def BookCover():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['recordId', 'ip']
    )
    data = HPULib.lib_book_cover(
        request.args['recordId'],
        False,
        request.args['ip']
    )
    return data


# 图书馆图书封面, 直接返回封面base64
# 接收: recordId
# 返回: data
@app.route('/lib/book/cover/raw/<recordId>', methods=['GET', 'POST'])
def BookCoverRaw(recordId=None):
    if not recordId:
        BaseException.ParameterException('缺少参数: recordId')
    data = HPULib.lib_book_cover(
        recordId,
        True
    )
    return data

# 根据书名和isbn查找封面
# 接收: title, isbn
# 返回: data
@app.route('/lib/book/cover/normal', methods=['GET', 'POST'])
def BookCoverNormal():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['title', 'isbn']
    )
    data = HPULib.lib_book_cover_normal(
        request.args['title'],
        request.args['isbn']
    )
    return jsonify({
        'msg': 'success',
        'data': data
    })


# 图书馆图书馆藏情况
# 接收: recordId, ip
# 返回: data
@app.route('/lib/book/collection', methods=['GET', 'POST'])
def BookCollection():
    BaseValidate.paramsExist(
        request.args.to_dict(),
        ['recordId', 'ip']
    )
    data = HPULib.lib_book_collection(
        request.args['recordId'],
        request.args['ip']
    )
    return jsonify(data)















# 全局错误处理
@app.errorhandler(Exception)
def framework_error(e):
    raise e
    return BaseException.framework_error(e)

if __name__ == "__main__":
    app.config['DEBUG'] = True
    app.run(port= 5022)
