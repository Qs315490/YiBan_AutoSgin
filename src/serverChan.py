try:
    import requests
except ModuleNotFoundError:
    print("缺少依赖! 请安装依赖！")


class ServerChan:
    def __init__(self, title: str, token: str) -> None:
        self.title = title
        self.token = token
        self.msgs = ""

    def send_msg(self, token="", msg=""):
        if msg == "":
            msg = self.msgs
        if token == "" and self.token == "":
            return self
        if token == "":
            token = self.token
        requests.get(
            f"https://sctapi.ftqq.com/{token}.send",
            params={"title": self.title, "desp": msg},
            timeout=5,
        )
        self.msgs=''
        return self

    def log(self, msg=""):
        if msg == "":
            return self
        print(msg)
        if self.msgs == "":
            self.msgs = msg
        else:
            self.msgs += f"\n{msg}"
        return self
