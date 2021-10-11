# logger.py

import logging
import os
import time


class MyLogging(object):

    def __init__(self):
        timestr = time.strftime('%Y%m%d%H', time.localtime(time.time()))
        lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../log/SME'))
        filename = lib_path + '/' + timestr + '.log'  # 日志文件的地址
        self.logger = logging.getLogger(__name__)  # 定义对应的程序模块名name
        # 这为清空当前文件的logging 因为logging会包含所有的文件的logging
        logging.Logger.manager.loggerDict.pop(__name__)
        # 将当前文件的handlers 清空
        self.logger.handlers = []
        # 然后再次移除当前文件logging配置
        self.logger.removeHandler(self.logger.handlers)
        #  这里进行判断，如果logger.handlers列表为空，则添加，否则，直接去写日志
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)  # 必须设置，这里如果不显示设置，默认过滤掉warning之前的所有级别的信息
            sh = logging.StreamHandler()  # 日志输出到屏幕控制台
            sh.setLevel(logging.INFO)  # 设置日志等级
            # 设置格式对象
            formatter = logging.Formatter(
                "%(asctime)s %(filename)s[line:%(lineno)d]%(levelname)s - %(message)s")  # 定义日志输出格式

            fh = logging.FileHandler(filename=filename, encoding='utf-8')  # 向文件filename输出日志信息
            fh.setLevel(logging.INFO)  # 设置日志等级

            # 设置handler的格式对象
            sh.setFormatter(formatter)
            fh.setFormatter(formatter)

            # 将handler增加到logger中
            self.logger.addHandler(sh)
            self.logger.addHandler(fh)


if __name__ == "__main__":
    log = MyLogging().logger
    log.debug("debug")
    log.info("info")
    log.warning("warning")
    log.error("error")
    log.critical("critical")
