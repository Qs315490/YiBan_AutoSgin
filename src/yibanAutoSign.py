import math
import os
import random
import re
import threading
import time
# from base64 import b64encode

from serverChan import ServerChan
from userData import user_data

try:
    import requests
    # from Crypto.Cipher import PKCS1_v1_5
    # from Crypto.PublicKey import RSA
except ModuleNotFoundError:
    print("缺少依赖! 请安装依赖！")

DEBUG = False
# 连接出错时重试次数
RESEND_COUNT = 3


def get_csrf_token():

    def token():
        a = math.floor(65536 * (1 + random.random()))
        return f'{a:x}'

    csrf_token = ''
    for _ in range(8):
        csrf_token += token()[1:]
    return csrf_token


# def encrypt_rsa(data: str) -> str:
#     """
#     登录密码加密
#     :param data: 待加密的密码
#     :return: str
#     """
#     rsa_key = '''-----BEGIN PUBLIC KEY-----
#     MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6aTDM8BhCS8O0wlx2KzA
#     Ajffez4G4A/QSnn1ZDuvLRbKBHm0vVBtBhD03QUnnHXvqigsOOwr4onUeNljegIC
#     XC9h5exLFidQVB58MBjItMA81YVlZKBY9zth1neHeRTWlFTCx+WasvbS0HuYpF8+
#     KPl7LJPjtI4XAAOLBntQGnPwCX2Ff/LgwqkZbOrHHkN444iLmViCXxNUDUMUR9bP
#     A9/I5kwfyZ/mM5m8+IPhSXZ0f2uw1WLov1P4aeKkaaKCf5eL3n7/2vgq7kw2qSmR
#     AGBZzW45PsjOEvygXFOy2n7AXL9nHogDiMdbe4aY2VT70sl0ccc4uvVOvVBMinOp
#     d2rEpX0/8YE0dRXxukrM7i+r6lWy1lSKbP+0tQxQHNa/Cjg5W3uU+W9YmNUFc1w/
#     7QT4SZrnRBEo++Xf9D3YNaOCFZXhy63IpY4eTQCJFQcXdnRbTXEdC3CtWNd7SV/h
#     mfJYekb3GEV+10xLOvpe/+tCTeCDpFDJP6UuzLXBBADL2oV3D56hYlOlscjBokNU
#     AYYlWgfwA91NjDsWW9mwapm/eLs4FNyH0JcMFTWH9dnl8B7PCUra/Lg/IVv6HkFE
#     uCL7hVXGMbw2BZuCIC2VG1ZQ6QD64X8g5zL+HDsusQDbEJV2ZtojalTIjpxMksbR
#     ZRsH+P3+NNOZOEwUdjJUAx8CAwEAAQ==
#     -----END PUBLIC KEY-----'''
#     data_byte = bytes(data, 'utf-8')
#     encrypt_obj = PKCS1_v1_5.new(RSA.importKey(rsa_key))
#     data_encrypt = b64encode(encrypt_obj.encrypt(data_byte))
#     return data_encrypt.decode('utf-8')


class YiBan:

    def __init__(self,
                 phone,
                 passwd,
                 address,
                 server_chan: ServerChan,
                 photo: str = '') -> None:
        self.phone = phone
        self.password = passwd
        self.CSRF = get_csrf_token()  # '64b5c616dc98779ee59733e63de00dd5'
        self.address = address
        self.session = requests.session()
        self.server_chan = server_chan
        self.photo = photo

    def req(self,
            url,
            method='get',
            cookies=None,
            headers=None,
            timeout=5,
            allow_redirects=True,
            **kwargs) -> requests.Response:
        if headers is None:
            headers = {}
        if cookies is None:
            cookies = {}
        data = kwargs.get('data')
        params = kwargs.get('params')
        cookies.update(self.session.cookies.get_dict())
        cookies.update({'csrf_token': self.CSRF})
        headers.update({
            "Origin": "https://c.uyiban.com",
            'AppVersion': '5.0',
            'User-Agent': 'Yiban'
        })
        if method == 'get':
            reqs = self.session.get
        elif method == 'post':
            reqs = self.session.post
        elif method == 'put':
            reqs = self.session.put
        else:
            self.session.close()  # close session
            raise Exception('Requests method error.')

        for i in range(RESEND_COUNT):
            try:
                back = reqs(url,
                            data=data,
                            params=params,
                            headers=headers,
                            cookies=cookies,
                            timeout=timeout,
                            allow_redirects=allow_redirects)
            except (requests.exceptions.RequestException):
                print(f'连接将被重置({i + 1}/{RESEND_COUNT})')
                time.sleep(5)
            else:
                return back
        raise Exception('连接异常且重试后失败')

    def do_login(self) -> bool:
        push_data = {'account': self.phone, 'password': self.password}
        # 这个请求没有返回值
        self.req('https://www.yiban.cn/login/dologinAjax',
                 'post',
                 data=push_data,
                 headers={
                     'Content-Type':
                     'application/x-www-form-urlencoded; charset=UTF-8'
                 }).json()
        try:
            self.session.cookies.get_dict()['yiban_user_token']
        except KeyError:
            self.server_chan.log(f'{self.phone} 登录失败')
            return False
        return True

    def auth(self) -> dict:
        """
        用户认证
        """
        url = ('iapp', 'iframe')
        back_raw = self.req(f'https://f.yiban.cn/{url[1]}/index?act=iapp7463',
                            allow_redirects=False)
        verify = re.findall(r"verify_request=(.*?)&",
                            back_raw.headers.get("Location"))[0]
        back_json = self.req('https://api.uyiban.com/base/c/auth/yiban',
                             params={
                                 'verifyRequest': verify,
                                 'CSRF': self.CSRF
                             }).json()
        try:
            back_json['data']['PersonName']
        except KeyError:
            msg = f'{self.phone} 获取授权失败, 可能未授权校本化.'
            self.server_chan.log(msg)
            return {'code': 1, 'msg': msg}
        return back_json

    def do_sign(self):
        """
        晚点名签到
        :return:
        """

        def get_status() -> dict:
            # 获取照片要求
            self.req(
                f'https://api.uyiban.com/nightAttendance/student/index/photoRequirements?CSRF={self.CSRF}'
            )
            # 设备状态?
            self.req(
                f'https://api.uyiban.com/nightAttendance/student/index/deviceState?CSRF={self.CSRF}'
            ).json()
            # 获取区域id
            self.req(
                f'https://api.uyiban.com/nightAttendance/student/index/getPersonId?CSRF={self.CSRF}'
            ).json()
            # 获取签到区域
            back_json = self.req(
                f'https://api.uyiban.com/nightAttendance/student/index/signPosition?CSRF={self.CSRF}'
            ).json()
            return back_json

        back_json = get_status()
        # 等待到达时间
        time_now = time.time()
        time_range = back_json['data']['Range']
        while time_now < time_range['StartTime'] and not DEBUG:
            time.sleep(1)
            time_now += 1

        get_status()  # 不加会按之前获取状态的时间, 从而导致失败

        if time_now < time_range['EndTime'] or DEBUG:
            photo_path = ''
            if self.photo != '':
                with open(self.photo, 'rb') as file:
                    photo_raw = file.read()

                photo_size = os.path.getsize(self.photo)
                # 上传照片
                back = self.req(
                    "https://api.uyiban.com/nightAttendance/student/index/uploadUri",
                    params={
                        "name": "image.jpg",
                        "type": "image/jpeg",
                        "size": str(photo_size),  #"99819", # 图片大小
                        "CSRF": self.CSRF
                    })
                try:
                    back_url = back['data']['signedUrl']
                    back = self.req(back_url,
                                    'put',
                                    data=photo_raw,
                                    headers={"Content-Type": "image/jpeg"})
                    print(self.phone, "照片上传返回", back)
                    photo_path = re.findall("night[\w/]*.jpg", back_url)[0]
                except KeyError:
                    msg = f'{self.phone} 照片上传失败'
                    self.server_chan.log(msg)
                    return msg

            push_data = {
                "AttachmentFileName":
                photo_path,  # "nightattendance/20221109/f574dd9907994825b40086e81d4f88ad.jpg",
                "Code": "",
                "PhoneModel": "",
                "SignInfo": self.address,
                "OutState": "1"
            }
            try:
                back = self.req(
                    f'https://api.uyiban.com/nightAttendance/student/index/signIn?CSRF={self.CSRF}',
                    'post',
                    data=push_data).json()
            except requests.exceptions.RequestException:
                msg = f'{self.phone} 网络或参数异常, 签到失败'
                self.server_chan.log(msg)
                return msg

            if back['code'] == 0 and back['data'] is True:
                msg = f'{self.phone} 签到成功'
            else:
                msg = f'{self.phone} 签到失败: {back["msg"]}'
                # print(back)
            self.server_chan.log(msg)
            return msg

        msg = f'{self.phone} 签到失败未到签到时间'
        self.server_chan.log(msg)
        return msg


def start_sign(user: YiBan):
    server_chan = ServerChan('易班签到详情', user['SendKey'])
    yiban = YiBan(user['Phone'], user['PassWord'], user['Address'],
                  server_chan)
    if not yiban.do_login():
        server_chan.send_msg()
        return
    if yiban.auth()['code'] != 0:
        server_chan.send_msg()
        return
    yiban.do_sign()
    server_chan.send_msg()


try:
    env = os.getenv('skip').split(',')
except AttributeError:
    env = ''

for user in user_data:
    if user['Phone'] in env:
        print(f'用户 {user["Phone"]} 在跳过列表')
        continue
    
    if DEBUG:
        start_sign(user)
    else:
        threading.Thread(target=start_sign, args=(user, )).run()
