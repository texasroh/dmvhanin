import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dmvhanin.config import Config

class Gmail():
    
    def __init__(self):
        self.acct = Config.GMAIL_ACCT
        self.pwd = Config.GMAIL_PWD
        self.smtp = Config.GMAIL_SMTP
        self.port = Config.GMAIL_PORT
        self.s = None
    
    def connect(self):
        if self.s is None:
            self.s = smtplib.SMTP(self.smtp, self.port)
            self.s.ehlo()
            self.s.starttls()
            self.s.login(self.acct, self.pwd)
        
    def close(self):
        if self.s is not None:
            self.s.quit()
            self.s = None
            
    def send(self, subject, email_to, text, html):
        self.connect()
        
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From'] = self.acct
        msg['To'] = email_to
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        self.s.sendmail(self.acct, email_to, msg.as_string())
        
        #self.close()
        
    def email_verify(self, email_to, hash):
        subject = '[DMV한인] 이메일 인증'
        
        verify_addr = "https://dmvhanin.com/auth/email_verify/{}".format(hash)
        
        text = '''\
        DMV한인에 가입하신것을 환영합니다.
        아래 링크를 클릭하시면 이메일 인증이 완료됩니다. 링크는 24시간만 유효합니다.
        {}
        링크 클릭이 안될시 복사해서 주소창에 붙여넣어주세요
        '''.format(verify_addr)
        
        html = '''\
        <html>
            <body>
                <p>DMV한인에 가입하신것을 환영합니다.</p>
                <p>아래 링크를 클릭하시면 이메일 인증이 완료됩니다. 링크는 24시간만 유효합니다.</p>
                <p><a href="{}">{}</a></p>
                <p>링크 클릭이 안될시 복사해서 주소창에 붙여넣어주세요</p>
            </body>
        </html>
        '''.format(verify_addr, verify_addr)
        
        self.send(subject, email_to, text, html)
        
    def email_find_user_id(self, email_to, user_id):
        subject = "[DMV한인] 아이디 찾기"
        
        text = '''\
        DMV한인 아이디
        {}
        '''.format(user_id)
        
        html = '''\
        <html>
            <body>
                <p>DMV한인 아이디</p>
                <p><b>{}</b></p>
            </body>
        </html>
        '''.format(user_id)
        
        self.send(subject, email_to, text, html)
    
    def email_tmp_password(self, email_to, tmp_password):
        subject = "[DMV한인] 임시 비밀번호 발급"
        
        text = '''\
        DMV한인 임시비밀번호
        {}
        로그인하셔서 비밀번호를 변경하세요
        '''.format(tmp_password)
        
        html = '''\
        <html>
            <body>
                <p>DMV한인 임시비밀번호</p>
                <p><b>{}</b></p>
                <p>로그인하셔서 비밀번호를 변경하세요</p>
            </body>
        </html>
        '''.format(tmp_password)
        
        self.send(subject, email_to, text, html)
        
        