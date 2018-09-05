#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/4 10:22
# @Author  : 
# @File    : weibo_login.py
# @Software: PyCharm

import os
import time
import pickle
from tqdm import *
from selenium import webdriver
from settings import config

# 方便完全加载登录页面
def count_time():
	for i in tqdm(range(40)):
		time.sleep(0.5)

driver = webdriver.Firefox(executable_path = "C:\driver\geckodriver.exe")
driver.set_window_size(1640, 688)
driver.get(config.LOGIN_URL)

# 在获取elment之前等待4s，等待页面渲染
count_time()

# 登录
driver.find_element_by_xpath('//input[@id="loginName"]').send_keys(config.ACCOUNT_ID)
driver.find_element_by_xpath('//input[@id="loginPassword"]').send_keys(config.ACCOUNT_PASSWORD)
print('account id: {}'.format(config.ACCOUNT_ID))
print('account password: {}'.format(config.ACCOUNT_PASSWORD))
driver.find_element_by_xpath('//a[@id="loginAction"]').click()

# 关于获取cookie的目的，比如登录有图形验证码，可以通过绕过验证码方式，添加cookie方法登录。
def save_cookile():
	try:
		cookie_list = driver.get_cookies()
		print(cookie_list)
		cookie_string = ''
		for cookie in cookie_list:
			if 'name' in cookie and 'value' in cookie:
				cookie_string += cookie['name'] + '=' + cookie['value'] + ';'
		print(cookie_string)
		if 'SSOLoginState' in cookie_string:
			print("成功获取cookie!\n{}".format(cookie_string))
			if os.path.exists(config.COOKIE_SAVE_PATH):
				os.remove(config.COOKIE_SAVE_PATH)

			cookie_dict = {}
			cookie_dict[config.ACCOUNT_ID] = cookie_string
			with open(config.COOKIE_SAVE_PATH, "wb") as f:
				pickle.dump(cookie_dict, f)
			print("成功保存cookie到文件{}\n".format(config.COOKIE_SAVE_PATH))

	except Exception as e:
		print(e)


if __name__ == '__main__':
	save_cookile()
