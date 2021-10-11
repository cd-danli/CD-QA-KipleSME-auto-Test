# coding = utf-8
import datetime
import json
import random

from interface_automation_V3.cd_api_test.common.db_util import MysqlDb
from interface_automation_V3.cd_api_test.common.logger import *
from interface_automation_V3.cd_api_test.common.request_util import RequestUtil
from interface_automation_V3.cd_api_test.common.send_mail import SendMail


# from lxml import etree


class TestCase:

    def __init__(self):
        self.log = MyLogging().logger

    def loadAllCaseByProject(self, project):
        """
        根据project加载全部测试用例
        :param project:
        :return:
        """
        self.log.info("*****loadAllCaseByProject")
        my_db = MysqlDb()
        sql = "select * from `{0}_testcases` where project='{1}' and run='yes'".format(project, project)
        self.log.info("loadAllCaseByProject sql is:" + sql)
        results = my_db.query(sql)
        self.log.info("loadAllCaseByProject is:" + str(results))
        return results

    def findCaseById(self, project, case_id):
        """
        根据id找测试用例
        :param case_id:
        :return:
        """
        self.log.info("*****findCaseById")
        my_db = MysqlDb()
        sql = "select * from `{0}_testcases` where id='{1}'".format(project, case_id)
        results = my_db.query(sql, state="one")
        return results

    def loadConfigByProjectAndKey(self, project, key):
        """
        根据project和key加载配置
        :param project:
        :param key:
        :return:
        """
        # self.log.info("*****loadConfigByProjectAndKey")
        my_db = MysqlDb()
        sql = "select * from `{0}_config` where project='{1}' and dict_key='{2}'".format(project, project, key)
        # self.log.info("loadConfigByProjectAndKey sql is:" + str(sql))
        results = my_db.query(sql, state="one")
        # self.log.info("loadConfigByProjectAndKey mysql result is:" + str(results))
        return results

    def updateResultByCaseId(self, project, response, is_pass, msg, case_id):
        """
        根据测试用例id，更新响应内容和测试内容
        :param response:
        :param is_pass:
        :param msg:
        :param case_id:
        :return:
        """
        self.log.info("*****updateResultByCaseId")
        my_db = MysqlDb()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # self.log.info(current_time)
        sql = "update `{0}_testcases` set response=\"{1}\", pass='{2}', msg='{3}', update_time='{4}' where id={5}". \
            format(project, str(response), is_pass, str(msg), current_time, case_id)
        self.log.info(sql)
        rows = my_db.execute(sql)
        return rows

    def deleteResultByProject(self, project):
        """
        :param project:
        :return:
        """
        self.log.info("*****deleteResultByProject")
        my_db = MysqlDb()
        sql = "update `{0}_testcases` set pass ='',msg='',response ='',update_time =null  where project='{0}'".format(
            project, project)
        # self.log.info(sql)
        rows = my_db.execute(sql)
        return rows

    def caseRunSummary(self, project):
        """
        case允许结果统计，成功，失败和无结果的数目
        :param project:
        :return:
        """
        self.log.info("*****caseRunSummary")
        my_db = MysqlDb()
        sql = "select sum(case when run ='yes' then 1 else 0 end) as total_account," \
              "sum(case when run ='yes' and pass ='Pass' then 1 else 0 end) as pass_count," \
              "sum(case when run ='yes' and pass ='Fail' then 1 else 0 end) as fail_count," \
              "sum(case when run ='yes' and pass ='' then 1 else 0 end) as norun_count " \
              "from {0}_testcases where project = '{1}'".format(project, project)
        result = my_db.query(sql)
        return result[0]

    def checkFailCase(self, project):
        """
        过滤不成功的cases,返回case数目和case细节
        :param project:
        :return:
        """
        results = []
        self.log.info("*****checkFailCase")
        my_db = MysqlDb()
        # 获取接口域名
        sql1 = "select count(*) as case_num from {0}_testcases where project ='{1}' and pass!='True' and run='yes'".format(
            project, project)
        cases_num = my_db.query(sql1)
        results.append(cases_num)
        sql2 = "select * from {0}_testcases where project ='{0}' and pass!='True' and run='yes'".format(project,
                                                                                                        project)
        cases = my_db.query(sql2)
        results.append(cases)
        return results

    def runCaseUpdateDB(self, project, cases, api_host_obj):
        """
        重跑一些没有结果和失败的case
        :param project:
        :return:
        """
        self.log.info("*****runCaseUpdateDB")

        for case in cases:
            try:
                is_pass = "Fail"
                # 执行用例
                response = self.runCase(project, case, api_host_obj)
                # 断言判断
                assert_msg = self.assertResponse(case, response)
                self.log.info("assert_msg:" + str(assert_msg))
                if assert_msg['is_pass'] == True:
                    is_pass = "Pass"
                # 更新结果存储数据库
                rows = self.updateResultByCaseId(project, response, is_pass, assert_msg['msg'], case['id'])
                self.log.info(str("更新结果 rows={0}".format(str(rows))))
            except Exception as e:
                msg = str("用例id={0},标题:{1},执行报错:{2}".format(case['id'], case['title'], str(e)))
                self.log.info(msg)
                rows = self.updateResultByCaseId(project, '', is_pass, str(e).replace("'", ""), case['id'])
                self.log.info(str("更新结果 rows={0}".format(str(rows))))

    def runAllCase(self, project):
        """
        执行全部用例的入口
        :param project:
        :return:
        """
        self.log.info("########start to run API automation#######")
        self.log.info("*****runAllCase")
        start_time = datetime.datetime.now().replace(microsecond=0)
        try:
            self.deleteResultByProject(project)
            # 获取接口域名
            api_host_obj = self.loadConfigByProjectAndKey(project, "host")
            # 获取全部用例
            results = self.loadAllCaseByProject(project)
            self.runCaseUpdateDB(project, results, api_host_obj)
        except Exception as e:
            self.log.info("测试遇到问题" + str(e))
        # 重跑失败的case
        rerun_cases = self.checkFailCase(project)
        if rerun_cases[0][0]['case_num'] > 0:
            self.log.info("########rerun fail test cases#######")
            self.runCaseUpdateDB(project, rerun_cases[1], api_host_obj)
        # 发送测试报告
        self.sendTestReport(start_time, project)
        self.log.info("########complete to run API automation#######")

    def runCase(self, project, case, api_host_obj):
        """
        执行单个用例
        :param case:
        :param api_host_obj:
        :return:
        """
        self.log.info("*****runCase")
        self.log.info("#####start to run case id: {0}".format(case['id']))
        # headers = json.loads(case['headers'])
        headers = json.loads(case['headers'])
        body = json.loads(case['request_body'])
        method = case['method']
        req_url = api_host_obj['dict_value'] + case['url']
        # 判断case的一些字段是否需要唯一值,或者通过读取config表进行获取
        for body_key in body:
            if body[body_key] == "$need_unique_num$":
                body[body_key] = str(self.get_unique())
                self.log.info("body unique num is:" + body[body_key])
            if "$unique_" in body[body_key]:
                namelist1 = body[body_key].split("_")
                body[body_key] = str(self.get_unique(namelist1[1], namelist1[2]))
            if "$config_" in body[body_key]:
                config_dict_1 = self.loadConfigByProjectAndKey(project, body_key)
                self.log.info("body:" + body[body_key] + "will be replaced to " + config_dict_1['dict_value'])
                body[body_key] = config_dict_1['dict_value']

        for header_key in headers:
            if headers[header_key] == "$need_unique_num$":
                headers[header_key] = str(self.get_unique())
                self.log.info("header unique num is:" + headers[header_key])
            if "$unique_" in headers[header_key]:
                namelist2 = headers[header_key].split("_")
                headers[header_key] = str(self.get_unique(namelist2[1], namelist2[2]))
            if "$config_" in headers[header_key]:
                config_dict_2 = self.loadConfigByProjectAndKey(project, header_key)
                self.log.info(
                    str("headers:" + headers[header_key] + "will be replaced to " + config_dict_2['dict_value']))
                headers[header_key] = config_dict_2['dict_value']
        # 是否有前置条件
        if case["pre_case_id"] > -1:
            self.log.info("有前置条件")

            pre_case_id = case['pre_case_id']
            pre_case = self.findCaseById(project, pre_case_id)
            # 递归调用
            # self.log.info("====================pre_case" + pre_case)
            pre_response = self.runCase(project, pre_case, api_host_obj)
            # 前置条件断言
            pre_assert_msg = self.assertResponse(pre_case, pre_response)
            if "success" in pre_assert_msg['msg']:
                self.log.info("前置条件通过")
            else:
                # 前置条件不通过直接返回
                pre_response['msg'] = "前置条件不通过," + pre_response['message']
                return pre_response

            # 判断需要case的前置条件是哪个字段
            pre_fields = json.loads(case['pre_fields'])
            for pre_field in pre_fields:
                self.log.info(pre_field)
                if pre_field['scope'] == 'header':
                    # 遍历headers ,替换对应的字段值，即寻找同名的字段
                    for header in headers:
                        field_name = pre_field['field']
                        if header == field_name:
                            field_value = pre_response['data'][field_name]
                            headers[field_name] = field_value
                            self.log.info("field_value:" + field_value)
                elif pre_field['scope'] == 'body':
                    self.log.info("替换body")
        self.log.info(
            str('case id = {0}\nreq_url = {1}\n method = {2}\n header = {3}\n param ={4}'.format(case['id'], req_url,
                                                                                                 method, headers,
                                                                                                 body)))
        # 发起请求
        req = RequestUtil()
        response = req.request(req_url, method, headers=headers, param=body, content_type="application/json")
        self.log.info("response = ↓")
        self.log.info(response)
        self.log.info("#####end to run case id: {0}".format(case['id']))
        return response

    def assertResponse(self, case, response):
        """
        断言响应内容，更新用例执行情况 {"is_pass":true, "msg":"code is wrong"}
        :param case:
        :param response:
        :return:
        """
        self.log.info("*****assertResponse")
        assert_type = case['assert_type']
        expect_result = case['expect_result']
        is_pass = False

        # 判断业务状态码
        if assert_type == 'code':
            response_code = response['code']
            if response_code == "success":
                response_code = 200
            if int(expect_result) == response_code:
                is_pass = True
                self.log.info("测试用例通过")
            else:
                self.log.info("测试用例不通过")
                is_pass = False
        elif assert_type == 'data_len':
            data = response['data']
            if data is not None and len(data) > int(expect_result):
                is_pass = True
                self.log.info("测试用例通过")
            else:
                self.log.info("测试用例不通过")
                is_pass = False

        elif assert_type == 'data_content':
            data = response['data']
            if data is not None and str(expect_result) in str(data):
                is_pass = True
                self.log.info("测试用例通过")
            else:
                self.log.info("测试用例不通过")
                is_pass = False

        msg = "module:{0},title:{1},assert_type:{2},message:{3}".format(case['module'], case['title'], assert_type,
                                                                        response['msg'])
        # 拼装信息
        assert_msg = {"is_pass": is_pass, "msg": msg}
        return assert_msg

    def loadHtmlPre(self):
        """
        获取测试报告前面部分
        :return:
        """
        self.log.info("*****loadHtmlPre")
        tmp_f = open("../template/report_pre.html", "r", encoding="utf-8")  # 读取文件
        f = tmp_f.read()  # 把文件内容转化为字符串
        return f

    def loadHtmlEnd(self):
        """
        获取测试报告前面部分
        :return:
        """
        self.log.info("*****loadHtmlEnd")
        tmp_f = open("../template/report_end.html", "r", encoding="utf-8")  # 读取文件
        f = tmp_f.read()  # 把文件内容转化为字符串
        return f

    def getResultData(self, start_time, project):
        """
        组装生成测试报告的数据
        :param start_time:
        :param project:
        :return:
        """
        self.log.info("*****getResultData")
        results = self.loadAllCaseByProject(project)
        case_summary = self.caseRunSummary(project)
        current_time = datetime.datetime.now().replace(microsecond=0)
        cost_time = current_time - start_time
        resultData = {}
        resultData['testName'] = str(project) + ' test report'
        resultData['testAll'] = str(case_summary['total_account'])
        resultData['testPass'] = str(case_summary['pass_count'])
        resultData['testFail'] = str(case_summary['fail_count'])
        resultData['beginTime'] = str(start_time)
        resultData['totalTime'] = str(cost_time)
        resultData['testSkip'] = str(case_summary['norun_count'])
        resultData['testError'] = str(case_summary['norun_count'])
        cases = self.loadAllCaseByProject(project)
        testResult = []
        each_testResult = {}
        for case in cases:
            each_testResult['module'] = case['module']
            each_testResult['apiname'] = case['title']
            each_testResult['description'] = case['title']
            each_testResult['QA'] = case['qa']
            each_testResult['status'] = case['pass']
            each_testResult['log'] = [str((case['response']))]
            testResult.append(each_testResult.copy())
        resultData['testResult'] = testResult
        return json.dumps(resultData)

    def sendTestReport(self, start_time, project):
        self.log.info("*****sendTestReport")
        title = "{0} API automation test report".format(project)
        mail_host = self.loadConfigByProjectAndKey(project, "mail_host")['dict_value']
        mail_sender = self.loadConfigByProjectAndKey(project, "mail_sender")['dict_value']
        mail_password = self.loadConfigByProjectAndKey(project, "mail_password")['dict_value']
        mail_receivers = self.loadConfigByProjectAndKey(project, "mail_receivers")['dict_value'].split(",")
        mail = SendMail()
        pre_content = self.loadHtmlPre()
        result_data = self.getResultData(start_time, project)
        end_content = self.loadHtmlEnd()
        content = pre_content + result_data + end_content
        # 取当前日期时间
        now_time = time.strftime("%Y-%m-%d_%H_%M_%S")
        filename = 'test_report_' + now_time + '.html'
        # base_path = os.path.dirname(os.getcwd())
        # html_report = base_path + '\\report\\' + project + '\\' + filename
        html_report = '../report/' + project + '/' + filename
        with open(html_report, 'w', encoding="utf-8") as name:
            name.write(content)
        mail.send(title, html_report, mail_host, mail_sender, mail_receivers, mail_password)

    def get_unique(self, name1=None, name2=None):
        """
        根据指定的name，和随机生成的数字，来拼接一个参数
        :param name:
        :return:
        """
        if name1 or name2:
            if name1 == 0:
                name1 = ""
            if name2 == 0:
                name2 = ""
            randint_data = str(name1) + random.randint(1000, 10000000) + str(name2)
        else:
            randint_data = random.randint(1000, 10000000)
        return randint_data
