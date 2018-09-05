#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/4 10:38
# @Author  : 
# @File    : weibo_scrapy_core.py
# @Software: PyCharm

import os
import re
import time
import logging
import pickle
import requests
import numpy as np
from lxml import etree
from settings import config
from util.db_relate import *

# 定义正则表达式, 提取数字
pattern = re.compile('\d+')

# 初始化
mongodb = Mongodb()

class WbScrapy(object):
    def __init__(self, scrap_id):
        self.scrap_id = scrap_id
        self.filter_flag=0
        # 预先定义好
        self.rest_time = 20  # 等待时间
        self.weibo_comment_detail_urls = []  # 微博评论地址
        self.weibo_content = []  # 微博内容
        self.weibo_num_zan_list = []  # 微博点赞数
        self.weibo_num_forward_list = []  # 微博转发数
        self.weibo_num_comment_list = []  # 微博评论数
        self.weibo_scraped = 0  # 抓取的微博条数
        self.rest_min_time = 10
        self.rest_max_time = 20

        self.scrapy_mark_save_file = os.path.join(config.SCRAPED_MARK_PATH, "scraped_id.pkl") # 已经爬取的种子id的保存
        self.weibo_content_save_file = os.path.join(config.CORPUS_SAVE_DIR, 'weibo_content.pkl') # 微博内容的保存
        self.weibo_fans_save_file = os.path.join(config.CORPUS_SAVE_DIR, 'weibo_fans.pkl') # 微博粉丝的保存
        self.scrapy_ids_file = os.path.join(config.CORPUS_SAVE_DIR, 'scrapy_ids.txt')  # 爬取的种子id的保存
        self.weibo_content_comment_save_file = os.path.join(config.CORPUS_SAVE_DIR, 'weibo_content_comment.pkl')

        self.get_cookies_by_account()
        self.request_header()
        self.user_name, self.weibo_num, self.gz_num, self.fs_num, self.page_num = self.get_weibo_baisc_info()

    # 加载cookie
    def get_cookies_by_account(self):
        with open(config.COOKIE_SAVE_PATH, 'rb') as f:
            cookie = pickle.load(f)
            # 未来抓取页面需要的可不登陆的cookie
            self.cookie = {
                "Cookie": cookie[config.ACCOUNT_ID]
            }

    # 获取请求的cookie和headers
    def request_header(self):
        # 避免被禁，获取头文件
        headers = requests.utils.default_headers()
        user_agent = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0"
        }
        headers.update(user_agent)
        self.headers = headers

    # 判断微博id是否被抓取过
    def judge_scapy_id(self):
        if os.path.exists(self.scrapy_mark_save_file):
            with open(self.scrapy_mark_save_file, "rb") as f:
                scraped_ids = pickle.load(f)
                if self.scrap_id in scraped_ids:
                    return True
                else:
                    return False
        return False

    # 获取微博的基本信息
    def get_weibo_baisc_info(self):
        crawl_url = 'http://weibo.cn/%s?filter=%s&page=1' % (self.scrap_id, self.filter_flag)
        print("抓取的页面是: {}".format(crawl_url))
        html = requests.get(crawl_url, cookies=self.cookie, headers=self.headers).content


        # 获取微博内容
        print("\n" + "-" * 30)
        print("准备获取微博内容：")
        selector = etree.HTML(html)

        try:
            # 获取微博名
            self.user_name = selector.xpath("//div/table//div/span[@class='ctt']/text()")[0]
            # print("user_name: ", user_name)

            # 获取微博其他信息
            # 总微博数
            weibo_num = selector.xpath("//div/span[@class='tc']/text()")[0]
            self.weibo_num = pattern.findall(weibo_num)[0]
            # print("weibo_num: ", weibo_num)
            # 关注数
            gz_num = selector.xpath("//div[@class='tip2']/a/text()")[0]
            self.gz_num = pattern.findall(gz_num)[0]
            # print("gz_num: ", gz_num)
            # 粉丝数
            fs_num = selector.xpath("//div[@class='tip2']/a/text()")[1]
            self.fs_num = pattern.findall(fs_num)[0]
            # print("fs_num: ", fs_num)

            print('当前新浪微博用户{}已经发布的微博数为{}, 他目前关注{}了微博用户, 粉丝数有 {}'.format(self.user_name, self.weibo_num, self.gz_num, self.fs_num))

            if selector.xpath("//*[@id='pagelist']/form/div/input[1]") is None:
                page_num = 1
            else:
                # page_num = list(selector.xpath("//*[@id='pagelist']/form/div/input[1]")[0].attrib.iteritems())
                # [('name', 'mp'), ('type', 'hidden'), ('value', '14483')]
                # 注意抓取的是字符类型
                self.page_num = int(selector.xpath("//*[@id='pagelist']/form/div/input[1]")[0].attrib["value"])
                print("总共的微博页数: ", self.page_num)

            return self.user_name, self.weibo_num, self.gz_num, self.fs_num, self.page_num
        except Exception as e:
            logging.error(e)

    # 保存微博内容
    def save_weibo_content(self, user_name, weibo_content, page):
        dump_obj = dict()
        if os.path.exists(self.weibo_content_save_file):
            with open(self.weibo_content_save_file, 'rb') as f:
                dump_obj = pickle.load(f)
            if self.scrap_id in dump_obj.keys():
                dump_obj[self.scrap_id]['weibo_content'].append(weibo_content)
                dump_obj[self.scrap_id]['last_scrap_page'] = page
            with open(self.weibo_content_save_file, 'wb') as f:
                pickle.dump(dump_obj, f)

        dump_obj[self.scrap_id] = {
            'weibo_content': weibo_content,
            'last_scrap_page': page
        }
        with open(self.weibo_content_save_file, 'wb') as f:
            pickle.dump(dump_obj, f)
        print('\n微博用户: {} \t 微博ID: {} '.format(user_name, self.scrap_id))
        print('[CHEER] 微博内容已经保存到 {}, 成功的完成抓取第{}页！！！\n'.format(self.weibo_content_save_file, page))

    def get_weibo_content(self):
        # # 获取微博基本信息
        # user_name, weibo_num, gz_num, fs_num, total_page_num = self.get_weibo_baisc_info()
        total_page_num = self.page_num

        try:
            start_page = 0
            # 判断之前是否抓取过，若抓取过判断是否可以增量抓取
            if os.path.exists(self.weibo_content_save_file):
                with open(self.weibo_content_save_file, "rb") as f:
                    content_dict = pickle.load(f)
                if self.scrap_id in content_dict.keys():
                    wb_content = content_dict[self.scrap_id]['weibo_content']
                    start_page = content_dict[self.scrap_id]['last_scrap_page']
                    # 总页数大于上次之前抓取的页数，因为最新的微博是在第一页，因此抓取的区间位于[0, page_num - start_page]
                    if total_page_num >= start_page:
                        print("之前已经抓取过，现在开始增量抓取。。。")
                        start_page = 0
                        page_num = total_page_num - start_page
                else:
                    page_num = total_page_num
            else:
                page_num = total_page_num

            # 开始进行抓取
            try:
                # for page in range(start_page + 1, page_num + 1):
                for page in range(start_page + 1, page_num + 1):
                    url = 'http://weibo.cn/%s?filter=%s&page=%s' % (str(self.scrap_id), str(self.filter_flag), str(page))
                    html_other = requests.get(url=url, cookies=self.cookie, headers=self.headers).content
                    selector_other = etree.HTML(html_other)
                    content = selector_other.xpath("//div[@class='c']")
                    print("***************************************************")
                    print("当前解析的是第{}页，总共{}页".format(page, page_num))

                    # 每5页暂停一会，防止被禁
                    if page % 5 == 0:
                        print("等待{}s，以免微博被禁！".format(self.rest_time))
                        time.sleep(self.rest_time)

                    # 只有10条数据，但是抓取有12条数据，因此需要进行删除
                    if len(content) > 3:
                        for i in range(0, len(content) - 2):

                            # 抓取的微博条数
                            self.weibo_scraped += 1

                            # 获取加密后的id, 方便后续提取评论等数据
                            detail = content[i].xpath("@id")[0]
                            comment_url = 'http://weibo.cn/comment/{}?uid={}&rl=0'.format(detail.split('_')[-1],
                                                                                          self.scrap_id)
                            self.weibo_comment_detail_urls.append(comment_url)

                            # print("div/a/text(): ", content[i].xpath("div/a/text()"))
                            # div/a/text():  ['赞[15]', '转发[4]', '评论[8]', '收藏']

                            # 点赞数
                            num_zan = content[i].xpath('div/a/text()')[-4]
                            num_zan = pattern.findall(num_zan)[0]
                            self.weibo_num_zan_list.append(num_zan)

                            # 转发数
                            num_forward = content[i].xpath('div/a/text()')[-3]
                            num_forward = pattern.findall(num_forward)[0]
                            self.weibo_num_forward_list.append(num_forward)

                            # 评论数
                            num_comment = content[i].xpath('div/a/text()')[-2]
                            num_comment = pattern.findall(num_comment)[0]
                            self.weibo_num_comment_list.append(num_comment)

                            # 判断全文是否展开
                            quanwen_string = content[i].xpath("div/span[@class='ctt']/a/text()")
                            # print("quanwen_string: ", quanwen_string)

                            if "全文" in quanwen_string:
                                index = quanwen_string.index("全文")
                                # print(index)
                                quanwen_url = content[i].xpath("div/span[@class='ctt']/a[%d]/@href" % (index+1))[0]
                                # print(quanwen_url)
                                quanwen_url = "https://weibo.cn" + quanwen_url
                                # print(quanwen_url)
                                html_quanwen = requests.get(url=quanwen_url, cookies=self.cookie, headers=self.headers).content
                                selector_quanwen = etree.HTML(html_quanwen)
                                weibo_text = selector_quanwen.xpath("//div/div/span[@class='ctt']")[0]
                                # weibo_text = weibo_text.xpath("text()")[0]
                                weibo_text = "".join(weibo_text.xpath("text()"))
                                self.weibo_content.append(weibo_text)
                                # print("1")
                                print("weibo_text: ", weibo_text)
                                # print("DONE!")

                            else:
                                weibo_text = content[i].xpath("div/span[@class='ctt']")[0]

                                # 获取当前节点文本
                                weibo_text = weibo_text.xpath("string(.)")
                                self.weibo_content.append(weibo_text)
                                # print(2)
                                print("weibo_text: ", weibo_text)
                                # print("DONE!")
                    self.save_weibo_content(self.user_name, self.weibo_content, page)
                    if page == page_num:
                        print("{}所有的微博内容均已爬取完毕！".format(self.user_name))
            except etree.XMLSyntaxError as e:
                print("*" * 20)
                print('=' * 20)
                print("微博用户{}的所有微博已经爬取!".format(self.user_name))
                print("总共发了{}条微博，总的点赞数{}，总的转发数{}，总的收藏数{}".format(len(self.weibo_content),
                                                                 np.sum(self.weibo_num_zan_list),
                                                                 np.sum(self.weibo_num_forward_list),
                                                                 np.sum(self.weibo_num_comment_list)))

                # 保存微博内容
                self.save_weibo_content(self.user_name, self.weibo_content, total_page_num)

            except Exception as e:
                logging.error(e)
                print('\n' * 2)
                print('=' * 20)
                print('微博用户 {} 出现内容抓取错误 {}.'.format(self.user_name, e))
                print("总共发了{}条微博，总的点赞数{}，总的转发数{}，总的收藏数{}".format(len(self.weibo_content),
                                                                 np.sum(self.weibo_num_zan_list),
                                                                 np.sum(self.weibo_num_forward_list),
                                                                 np.sum(self.weibo_num_comment_list)))
                print('现在尝试保存微博内容...')
                self.save_weibo_content(self.user_name, self.weibo_content, page)

            print('\n' * 2)
            print('=' * 20)
            print("总共发了{}条微博，总的点赞数{}，总的转发数{}，总的收藏数{}".format(len(self.weibo_content),
                                                             np.sum(self.weibo_num_zan_list),
                                                             np.sum(self.weibo_num_forward_list),
                                                             np.sum(self.weibo_num_comment_list)))
            print('尝试保存微博内容...')
            # self.save_weibo_content(self.user_name, self.weibo_content, page)
            del self.weibo_content
            if self.filter_flag == 0:
                print('共' + str(self.weibo_scraped) + '条微博')
            else:
                print('共' + str(self.weibo_num) + '条微博，其中' + str(self.weibo_scraped) + '条为原创微博')

        except IndexError as e:
            print('已经获取完微博信息, 当前微博用户{}还没有发布微博.'.format(self.scrap_id))
        except KeyboardInterrupt:
            print('手动中止... 现在保存微博内容！')
            self.save_weibo_content(self.user_name, self.weibo_content, page - 1)


    # 保存要爬取的id以及对应的粉丝id
    def get_fans_id(self):
        fans_ids = []
        # 粉丝数小于200停止
        if self.fs_num < 200 :
            pass

        # 检查文件
        if os.path.exists(self.weibo_fans_save_file):
            with open(self.weibo_fans_save_file, "rb") as f:
                fans_ids = pickle.load(f)

        fans_url = "http://weibo.cn/{}/fans".format(self.scrap_id)
        print("查询粉丝的web网址：", fans_url)

        html_fans = requests.get(url=fans_url, cookies=self.cookie, headers=self.headers).content
        selector_fans = etree.HTML(html_fans)

        try:
            if selector_fans.xpath("//input[@name='mp']") is None:
                page = 1
            else:
                page_num = int(selector_fans.xpath("//input[@name='mp']")[0].attrib["value"])
                print("粉丝数的总页数为：{}".format(page_num))

            try:
                for i in range(1, page_num + 1):
                    # 每5页暂停一会，防止被禁
                    if i % 5 == 0:
                        print("等待{}s，以免微博被禁！".format(self.rest_time))
                        time.sleep(self.rest_time)

                    fans_url_child = 'https://weibo.cn/{}/fans?page={}'.format(self.scrap_id, i)
                    print('请求的子fans的url地址为: {}'.format(fans_url_child))
                    html_child = requests.get(fans_url_child, cookies=self.cookie, headers=self.headers).content
                    selector_child = etree.HTML(html_child)
                    fans_ids_content = selector_child.xpath("//div[@class='c']/table//a[1]/@href")
                    ids = [i.split("/")[-1] for i in fans_ids_content]
                    ids = list(set(ids))
                    print(ids)
                    for d in ids:
                        print('增加粉丝id {}'.format(d))
                        fans_ids.append(d)

            except Exception as e:
                print('error: ', e)
                dump_fans_list = list(set(fans_ids))
                print(dump_fans_list)
                with open(self.weibo_fans_save_file, 'wb') as f:
                    pickle.dump(dump_fans_list, f)
                print('粉丝id没有完全获取，部分粉丝id已经保存到 {}'.format(self.weibo_fans_save_file))

            dump_fans_list = list(set(fans_ids))
            print(dump_fans_list)
            with open(self.weibo_fans_save_file, 'wb') as f:
                pickle.dump(dump_fans_list, f)
            print('成功的将粉丝id保存到{}中！！！'.format(self.weibo_fans_save_file))

        except Exception as e:
            logging.error(e)


    # 保存微博内容和评论数据
    def get_content_comment(self):
        print('\n' + '-' * 30)
        print('正在获取微博和评论...')
        weibo_comment_detail_urls = self.weibo_comment_detail_urls  # 包含微博评论和微博正文的地址
        start_scrap_index = 0
        content_and_comment = []
        end_scrap_index = len(weibo_comment_detail_urls)

        if os.path.exists(self.weibo_content_save_file):
            print("从{}加载之前爬取的微博内容：".format(self.weibo_content_save_file))
            with open(self.weibo_content_save_file, "rb") as f:
                content_obj = pickle.load(f)
                self.weibo_content = content_obj[self.scrap_id]['weibo_content']

        if os.path.exists(self.weibo_content_comment_save_file) > 0:
            with open(self.weibo_content_comment_save_file, 'rb') as f:
                content_comment_obj = pickle.load(f)
                if self.scrap_id in content_comment_obj.keys():
                    obj = content_comment_obj[self.scrap_id]
                    weibo_detail_urls = content_comment_obj['weibo_detail_urls']
                    start_scrap_index = content_comment_obj['last_scrap_index']
                    content_and_comment = content_comment_obj['content_and_comment']

        try:
            for i in range(start_scrap_index + 1, end_scrap_index):
                url = weibo_comment_detail_urls[i]
                # url = "https://weibo.cn/comment/GxDsMsScc?uid=1618051664&rl=0"
                one_content_and_comment = dict()

                print("开始从url{}解析微博内容：".format(url))
                print("开始处理No {}, 微博总数量为{}".format(i, end_scrap_index))
                html_detail = requests.get(url=url, cookies=self.cookie, headers=self.headers).content
                selector_detail = etree.HTML(html_detail)

                # 如果当前微博没有评论，跳过它
                if selector_detail.xpath("//div[@id='pagelist']//div/input[1]/@value") is None:
                    continue
                else:
                    all_comment_pages = int(selector_detail.xpath("//div[@id='pagelist']//div/input[1]/@value")[0])
                    print(all_comment_pages)

                print('这是{}的微博：'.format(self.user_name))
                print('微博内容： {}'.format(self.weibo_content[i]))
                print('接下来是下面的评论：\n\n')

                one_content_and_comment['content'] = self.weibo_content[i]
                one_content_and_comment['comment'] = []

                start_idx = 0
                end_idx = all_comment_pages - 2

                for page in range(1, end_idx):
                    print("当前解析的页面是{}, 总页面{}。".format(page, end_idx))
                    # 每隔5页，稍微暂停
                    if page % 5 == 0:
                        rest_time = np.random.randint(self.rest_min_time, self.rest_max_time)
                        time.sleep(rest_time)

                    # 从第二页开始爬取，第一页有一些噪音
                    detail_comment_url = url + "&page=" + str(page + 1)
                    print(detail_comment_url)

                    # 开始解析页面
                    html_detail_page = requests.get(url=detail_comment_url, cookies=self.cookie, headers=self.headers).content
                    selector_comment_detail = etree.HTML(html_detail_page)
                    # starts-with 顾名思义，匹配一个属性开始位置的关键字; contains匹配一个属性值中包含的字符串
                    comment_list = selector_comment_detail.xpath("//div[starts-with(@id, 'C_')]")
                    for comment in comment_list:
                        single_comment_user_name = comment.xpath("a[1]/text()")[0]
                        # count: Returns the number of nodes for a given XPath  返回指定xpath的节点数
                        if comment.xpath('span[1][count(*)=0]'):
                            single_comment_content = comment.xpath('span[1][count(*)=0]/text()')[0]
                        else:
                            span_element = comment.xpath('span[1]')[0]
                            at_user_name = span_element.xpath('a/text()')[0]
                            at_user_name = '$' + at_user_name.split('@')[-1] + '$'
                            single_comment_content = span_element.xpath('/text()')
                            single_comment_content.insert(1, at_user_name)
                            single_comment_content = ' '.join(single_comment_content)

                        full_single_comment = '<' + single_comment_user_name + '>' + ': ' + single_comment_content
                        print(full_single_comment)
                        one_content_and_comment['comment'].append(full_single_comment)
                        one_content_and_comment['last_idx'] = page

            self.save_content_comment(url, i, one_content_and_comment)
        except Exception as e:
            logging.error('在调用方法get_content_comment()来获取微博内容和评论的过程中抛出异常, error:', e)
            print('\n' * 2)
            print('=' * 20)

    def save_content_comment(self, weibo_comment_detail_urls, i, one_content_and_comment):
        # 暂时先不考虑已经爬取过，然后重新更新数据的问题
        dump_dict = dict()
        dump_dict[self.scrap_id] = {
            'weibo_detail_urls': weibo_comment_detail_urls,
            'last_scrap_index': i,
            'content_and_comment': one_content_and_comment
        }
        with open(self.weibo_content_comment_save_file, "wb") as f:
            print("保存微博内容和评论中。。。")
            pickle.dump(dump_dict, f)



    # 抓取微博正文和评论并保存到mongodb中
    def get_content_and_comment_to_db(self, limit=10):
        # 开始进行抓取, 出于简单考虑这里不考虑抓取过

        start_page = 0
        try:

            for page in range(start_page + 1, self.page_num + 1):
                url = 'http://weibo.cn/%s?filter=%s&page=%s' % (str(self.scrap_id), str(self.filter_flag), str(page))
                html_other = requests.get(url=url, cookies=self.cookie, headers=self.headers).content
                selector_other = etree.HTML(html_other)
                content = selector_other.xpath("//div[@class='c']")
                print("***************************************************")
                print("当前解析的是第{}页，总共{}页".format(page, self.page_num))

                # 每5页暂停一会，防止被禁
                if page % 5 == 0:
                    print("等待{}s，以免微博被禁！".format(self.rest_time))
                    time.sleep(self.rest_time)

                # 只有10条数据，但是抓取有12条数据，因此需要进行删除
                if len(content) > 3:
                    for i in range(0, len(content) - 2):

                        # 抓取的微博条数
                        self.weibo_scraped += 1

                        # 获取加密后的id, 方便后续提取评论等数据
                        detail = content[i].xpath("@id")[0]
                        comment_url = 'http://weibo.cn/comment/{}?uid={}&rl=0'.format(detail.split('_')[-1],
                                                                                      self.scrap_id)
                        self.weibo_comment_detail_urls.append(comment_url)

                        # 点赞数
                        num_zan = content[i].xpath('div/a/text()')[-4]
                        num_zan = pattern.findall(num_zan)[0]
                        self.weibo_num_zan_list.append(num_zan)

                        # 转发数
                        num_forward = content[i].xpath('div/a/text()')[-3]
                        num_forward = pattern.findall(num_forward)[0]
                        self.weibo_num_forward_list.append(num_forward)

                        # 评论数
                        num_comment = content[i].xpath('div/a/text()')[-2]
                        num_comment = pattern.findall(num_comment)[0]
                        self.weibo_num_comment_list.append(num_comment)

                        # 判断全文是否展开
                        quanwen_string = content[i].xpath("div/span[@class='ctt']/a/text()")

                        if "全文" in quanwen_string:
                            index = quanwen_string.index("全文")
                            quanwen_url = content[i].xpath("div/span[@class='ctt']/a[%d]/@href" % (index + 1))[0]
                            quanwen_url = "https://weibo.cn" + quanwen_url
                            html_quanwen = requests.get(url=quanwen_url, cookies=self.cookie,
                                                        headers=self.headers).content
                            selector_quanwen = etree.HTML(html_quanwen)
                            weibo_text = selector_quanwen.xpath("//div/div/span[@class='ctt']")[0]
                            weibo_text = "".join(weibo_text.xpath("text()"))
                            self.weibo_content.append(weibo_text)

                        else:
                            weibo_text = content[i].xpath("div/span[@class='ctt']")[0]

                            # 获取当前节点文本
                            weibo_text = weibo_text.xpath("string(.)")
                            self.weibo_content.append(weibo_text)

                        # 抓取评论数据
                        print("正在获取对应的评论数据。。。")
                        content_and_comment_dict = {}
                        print("开始从{}解析微博评论：".format(comment_url))


                        html_detail = requests.get(comment_url, cookies=self.cookie, headers=self.headers).content
                        selector_detail = etree.HTML(html_detail)

                        # 如果当前微博没有评论，跳过它
                        if selector_detail.xpath("//div[@id='pagelist']//div/input[1]/@value") is None:
                            continue
                        else:
                            all_comment_pages = int(selector_detail.xpath("//div[@id='pagelist']//div/input[1]/@value")[0])
                            print(all_comment_pages)

                        print('这是{}的微博：'.format(self.user_name))
                        print('微博内容： {}'.format(weibo_text))
                        print('接下来是下面的评论：\n\n')

                        content_and_comment_dict["content"] = weibo_text
                        content_and_comment_dict["comment"] = []
                        content_and_comment_dict["url"] = comment_url

                        # start_idx = 0
                        # 限制抓取指定数量的评论
                        end_idx = all_comment_pages - 2
                        if end_idx > limit:
                            end_idx = limit

                        for page in range(1, end_idx):
                            print("当前解析的页面是{}, 总页面{}。".format(page, end_idx))
                            # 每隔5页，稍微暂停
                            if page % 5 == 0:
                                rest_time = np.random.randint(self.rest_min_time, self.rest_max_time)
                                time.sleep(rest_time)

                            # 从第二页开始爬取，第一页有一些噪音
                            detail_comment_url = comment_url + "&page=" + str(page + 1)
                            print(detail_comment_url)

                            # 开始解析页面
                            html_detail_page = requests.get(url=detail_comment_url, cookies=self.cookie,
                                                            headers=self.headers).content
                            selector_comment_detail = etree.HTML(html_detail_page)
                            # starts-with 顾名思义，匹配一个属性开始位置的关键字; contains匹配一个属性值中包含的字符串
                            comment_list = selector_comment_detail.xpath("//div[starts-with(@id, 'C_')]")

                            for comment in comment_list:
                                single_comment_user_name = comment.xpath("a[1]/text()")[0]
                                # count: Returns the number of nodes for a given XPath  返回指定xpath的节点数
                                if comment.xpath('span[1][count(*)=0]'):
                                    single_comment_content = comment.xpath('span[1][count(*)=0]/text()')[0]
                                else:
                                    span_element = comment.xpath('span[1]')[0]
                                    at_user_name = span_element.xpath('a/text()')[0]
                                    at_user_name = '$' + at_user_name.split('@')[-1] + '$'
                                    single_comment_content = span_element.xpath('/text()')
                                    single_comment_content.insert(1, at_user_name)
                                    single_comment_content = ' '.join(single_comment_content)

                                full_single_comment = '<' + single_comment_user_name + '>' + ': ' + single_comment_content
                                print(full_single_comment)
                                content_and_comment_dict['comment'].append(full_single_comment)
                                content_and_comment_dict['last_idx'] = page

                        mongodb.insert(content_and_comment_dict)

        except Exception as e:
            logging.error('在获取微博内容和评论的过程中抛出异常, error:', e)
            print('\n' * 2)
            print('=' * 20)



if __name__ == "__main__":
    wb_scrapy = WbScrapy(scrap_id=1742566624)
    # wb_scrapy.get_weibo_content()
    wb_scrapy.get_content_and_comment_to_db()