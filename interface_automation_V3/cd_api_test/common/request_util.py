import requests

from interface_automation_V3.cd_api_test.common.logger import *

"""
Http工具类封装
"""


class RequestUtil:

    def __init__(self):
        self.log = MyLogging().logger

    def request(self, url, method, headers=None, param=None, content_type=None):
        """
        通用请求工具类
        :param url:
        :param method:
        :param headers:
        :param param:
        :param content_type:
        :return:
        """
        try:
            if method == 'get':
                result = requests.get(url=url, params=param, headers=headers, timeout=60).json()
                return result
            elif method == 'post':
                if content_type == 'application/json':
                    result = requests.post(url=url, json=param, headers=headers, timeout=60).json()
                    return result
                else:
                    self.log.info("url:" + url + "data:" + str(param) + "header:" + str(headers))
                    result = requests.post(url=url, data=param, headers=headers, timeout=60).json()
                    return result
            else:
                self.log.info("http method not allowed")

        except Exception as e:
            self.log.info(str("http请求报错:{0}".format(e)))

