class Bilibili:
    def __init__(self, username, password):
        self.__cookie = None
        self.__username = username
        self.__password = password

    def login(self):
        pass

    def cookie(self):
        if self.__cookie is None:
            self.login()
        return self.__cookie
