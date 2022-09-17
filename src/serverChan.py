try:
    import requests
except ModuleNotFoundError:
    print("缺少依赖! 请安装依赖！")


class ServerChan:
    def __init__(self, title: str, token: str) -> None:
        self.title = title
        self.token = token
        self.msgs = ''

    def send_msg(self, token='', msg=''):
        if msg == '':
            msg = self.msgs
        if token == '' and self.token == '':
            return
        if token == '':
            token = self.token
        requests.get('https://sctapi.ftqq.com/%s.send' %
                     token, params={'title': self.title, 'desp': msg})

    def log(self, msg=''):
        if msg == '':
            return
        print(msg)
        if self.msgs == '':
            self.msgs = msg
        else:
            self.msgs += f'\n{msg}'
