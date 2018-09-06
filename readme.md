# 微博数据爬取

说明：
1. settings/config下需要编辑自己的微博账户和密码

2. 执行如下生成cookies   
`python3 weibo_login.py`  

3. 具体内容或者评论爬取，启动方式：   
`python3 weibo_scrapy.py`   
注意：   
1). 需要指定爬取的种子scrap_id，可以直接在微博页面找寻
可以在weibo_scrapy.py中修改只是获取内容还是获取内容和评论
```
if __name__ == "__main__":
    wb_scrapy = WbScrapy(scrap_id=1742566624)
	# 获取内容，写到pickle中
    # wb_scrapy.get_weibo_content()
    # 获取内容和评论，并写道mongodb中
    # wb_scrapy.get_content_and_comment_to_db(limit=10)
```
2). 由于某些评论数据特别多，因此可以指定爬取多少页的评论。这里limit限定爬取多少页
`wb_scrapy.get_content_and_comment_to_db(limit=10)`

爬取微博内容的结果如下： 
```
准备获取微博内容：
当前新浪微博用户思想聚焦已经发布的微博数为73166, 他目前关注1702了微博用户, 粉丝数有 25231899
总共的微博页数:  7361
***************************************************
当前解析的是第1页，总共7361页
正在获取对应的评论数据。。。
开始从http://weibo.cn/comment/EwLwbivqE?uid=1742566624&rl=0解析微博评论：
3891
这是思想聚焦的微博：
微博内容： 尚未佩妥剑，转眼便江湖。愿历尽千帆，归来仍少年。[心] ​​​
接下来是下面的评论：

当前解析的页面是1, 总页面10。
http://weibo.cn/comment/EwLwbivqE?uid=1742566624&rl=0&page=2
<用户6409861410>: 1223440847
<用户6409861410>: $第柒人称-$
<如援知非>: $Hi亲爱的路人乙$
<深沉祖宗的玺子哥>: $子子子禾$
<biubiubiu哈哈哈>: $Promise她说$
<Promise她说>: $biubiubiu哈哈哈$
<biubiubiu哈哈哈>: $Promise她说$
<Promise她说>: $biubiubiu哈哈哈$
<赵八口ing>: 赚钱才是王道！
<biubiubiu哈哈哈>: $Promise她说$
当前解析的页面是2, 总页面10。
```