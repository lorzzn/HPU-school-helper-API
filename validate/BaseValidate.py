import json
import server
from exception import BaseException

class MissArgs(Exception):
    pass

def paramsExist(params:dict, keys:list):
    for key in keys:
        if key not in params:
            raise BaseException.ParameterException(f'缺少参数: {key}') 


