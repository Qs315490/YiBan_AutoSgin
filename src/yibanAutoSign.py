"""
new Env(易班自动签到)
cron: 59 20 * * *
"""

import os
import sys
import threading
import time

from serverChan import ServerChan
from userData import user_data
from yiban import Yiban

count = 3


def start_sign(user: dict):
    server_chan = ServerChan("易班签到详情", user["SendKey"])
    for i in range(count):
        yb = Yiban(user["Phone"], user["PassWord"])
        try:
            time_range = yb.task_feedback.get_sign_task()
        except Exception as e:
            # 一般是登录失败或登录超时
            print(e)
            print(f"{user['Phone']}出现错误, 尝试重新启动流程({i + 1}/{count})")
            time.sleep(2)
            # 重新进行登录操作
            continue
        while not time_range["StartTime"] < time.time() < time_range["EndTime"]:
            time.sleep(1)
        back = yb.submit_sign_feedback(user["Address"])
        server_chan.log(f'{user["Phone"]}: {back}').send_msg()
        return
    server_chan.log(f'{user["Phone"]}重试机会使用完').send_msg()


DEBUG = True if sys.gettrace() else False

if __name__ == "__main__":
    env = os.getenv("skip")
    if env is not None:
        env = env.split(",")
    else:
        env = ""

    for user in user_data:
        if user["Phone"] in env or not user.get("enable", True):
            print(f'用户 {user["Phone"]} 在跳过列表')
            continue

        if DEBUG:
            start_sign(user)
        else:
            threading.Thread(target=start_sign, args=(user,)).start()
