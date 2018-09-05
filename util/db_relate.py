#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/5 8:47
# @Author  : 
# @File    : db_relate.py
# @Software: PyCharm

import pymysql
from pymongo import MongoClient
from sqlalchemy import create_engine
from settings import config

# 这里未用到mysql，因此注释掉
# def write_to_mysql(df, table_name):
#     string = "mysql+pymysql://%s:%s@%s:%s/%s?charset=%s" % (config.DB_USERNAME, config.DB_PASSWORD,
#                                                             config.DB_HOST, config.DB_PORT, config.DB_DATABASE, config.DB_CODING)
#     engine = create_engine(string)
#     df.to_sql(name=table_name, con=engine, if_exists='append', index=False, index_label=False)


class Mongodb(object):
    def __init__(self):
        self.conn = MongoClient('localhost', 27017)
        self.db = self.conn.weibo_data  # 连接weibo_data数据库，没有则自动创建
        self.weibo_info = self.db.weibo_content_comment # 使用test_set集合，没有则自动创建

    def insert(self, record_dict):
        # 插入一条记录
        self.weibo_info.insert_one(record_dict)
        print("插入成功！")

        # # 插入多条记录 record_dict_list
        # self.weibo_info.insert_many(record_dict_list)
