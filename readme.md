# 微博数据爬取

说明：
1. settings/config下需要编辑自己的微博账户和密码

启动方式：   
`python3 weibo_scrapy.py`   
注意：
1. 需要指定爬取的种子scrap_id，可以直接在微博页面找寻
可以在weibo_scrapy.py中修改只是获取内容还是获取内容和评论
```
if __name__ == "__main__":
    wb_scrapy = WbScrapy(scrap_id=1742566624)
	# 获取内容，写到pickle中
    # wb_scrapy.get_weibo_content()
    # 获取内容和评论，并写道mongodb中
    # wb_scrapy.get_content_and_comment_to_db(limit=10)
```
2. 由于某些评论数据特别多，因此可以指定爬取多少页的评论。这里limit限定爬取多少页
`wb_scrapy.get_content_and_comment_to_db(limit=10)`
