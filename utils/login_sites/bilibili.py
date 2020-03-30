from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep


class Bilibili:
    def __init__(self, username, password):
        self.__cookie = None
        self.__url = 'https://passport.bilibili.com/login'
        options = ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.__browser = Chrome(options=options)
        self.__wait = WebDriverWait(self.__browser, 5, 0.2)
        self.__username = username
        self.__password = password

    def login(self):
        self.__browser.get(self.__url)
        username = self.__wait.until(expected_conditions.element_to_be_clickable((By.ID, 'login-username')))
        password = self.__wait.until(expected_conditions.element_to_be_clickable((By.ID, 'login-passwd')))
        username.send_keys(self.__username)
        password.send_keys(self.__password)

        slider = self.__wait.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'gt_slider_knob')))

    def cookie(self):
        if self.__cookie is None:
            self.login()
        return self.__cookie
