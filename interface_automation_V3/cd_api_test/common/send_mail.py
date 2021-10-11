# coding = utf-8

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from interface_automation_V3.cd_api_test.common.logger import *


class SendMail:

    def __init__(self):
        self.log = MyLogging().logger

    def send(self, title, report, mail_host, mail_sender, mail_receivers, mail_password):
        self.log.info("title = " + str(title) + " report = " + str(report) + " mail_host = " + str(mail_host) +
                      " mail_sender = " + str(mail_sender) + " mail_receivers = " + str(mail_receivers) +
                      " mail_password = " + str(mail_password))
        msg = MIMEMultipart('mixed')
        msg['Subject'] = title
        msg['from'] = str(mail_sender)
        msg['To'] = ";".join(mail_receivers)
        # 读取文件
        with open(report, 'rb') as f:
            send_att = f.read()
        att = MIMEText(send_att, 'html', 'utf-8')
        # 创建邮件内容
        text = "Hi ALL：\n\n" \
               "This is API automation test report which was sent automatically, " \
               "Please check the attachment for details. \n\n" \
               "Sincerely,\n" \
               "QA team,\n"
        text_plain = MIMEText(text, 'plain', 'utf-8')
        msg.attach(text_plain)
        # 发送附件
        att["Content-Type"] = 'application/octet-stream'
        att['Content-Disposition'] = 'attachment; filename = %s' % (report)
        msg.attach(att)
        # 发送邮件
        smtp = smtplib.SMTP()
        smtp.connect(mail_host)
        smtp.login(mail_sender, mail_password)
        try:
            smtp.sendmail(mail_sender, mail_receivers, msg.as_string())
            self.log.info('email was sent successfully!')
        except smtplib.SMTPException:
            self.log.info('fail to send this email!')
        finally:
            smtp.quit()
