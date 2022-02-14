from werkzeug.exceptions import HTTPException
from flask import jsonify, json, request

from controller.confutil import server


class APIException(HTTPException):
    code = 500
    msg = 'sorry, we made a mistake!'
    error_code = 999
 
    def __init__(self, msg=None, code=None, error_code=None,
                 headers=None):
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        if msg:
            self.msg = msg
        super(APIException, self).__init__(msg, None)
 
    def get_body(self, environ=None):
        body = dict(
            msg=self.msg,
            error_code=self.error_code,
            request=request.method + ' ' + self.get_url_no_param()
        )
        text = json.dumps(body)
        return text
 
    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]
 
    @staticmethod
    def get_url_no_param():
        full_path = str(request.full_path)
        main_path = full_path.split('?')
        return main_path[0] 


class Success(APIException):
    code = 201
    msg = 'ok'
    error_code = 0
 
class DeleteSuccess(Success):
    code = 202
    error_code = 1
 
class ServerError(APIException):
    code = 500
    msg = 'sorry, we made a mistake!'
    error_code = 999
 
class ClientTypeError(APIException):
    # 400 401 403 404
    # 500
    # 200 201 204
    # 301 302
    code = 400
    msg = 'client is invalid'
    error_code = 1006
 
class ParameterException(APIException):
    code = 400
    msg = 'invalid parameter'
    error_code = 1000
 
class NotFound(APIException):
    code = 404
    msg = 'the resource is not found'
    error_code = 1001
 
class AuthFailed(APIException):
    code = 401
    error_code = 1005
    msg = 'authorization failed'
 
class Forbidden(APIException):
    code = 403
    error_code = 1004
    msg = 'forbidden, not in scope'


def framework_error(e):
    if isinstance(e, APIException):
        return e
    if isinstance(e, HTTPException):
        code = e.code
        msg = e.description
        error_code = 1007
        return APIException(msg, code, error_code)
    else:
        # 调试模式
        # return ServerError()
        # log
        if not server.app.config['DEBUG']:
            return ServerError()
        else:
            raise e
            
            








