import requests
import logging
import logging.config
import yaml
import json
import math
import redis
import time
import random
import os


class DouBanMovieSpider:
    def __init__(self):
        """
        爬虫初始化
        :param token: init user
        """
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/63.0.3239.108 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Host": "www.douban.com",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            'Connection': 'keep-alive',
            'Accept-Language': 'zh,en;q=0.9,zh-CN;q=0.8,en-US;q=0.7',
        }

        # 初始化log
        try:
            log_config_file_path = '../log/movie_log_config.yaml'
            with open(log_config_file_path, 'r') as f:
                log_config = yaml.load(f)
                logging.config.dictConfig(log_config)
            self.movie_spider_log = logging.getLogger('spider')
            self.movie_spider_log.info('Logger初始化成功')
        except Exception as err:
            print('Logger初始化失败' + str(err))

        # 初始化配置
        try:
            spider_cofig_file_path = 'movie_spider_config.yaml'
            with open(spider_cofig_file_path, 'r') as f:
                spider_config = yaml.load(f)
                self.config = spider_config
                self.movie_spider_log.info('Config初始化成功')
        except Exception as err:
            self.movie_spider_log.error('Config初始化失败' + str(err))

        # 初始化redis
        try:
            redis_host = self.config['redis']['host']
            redis_port = self.config['redis']['port']
            self.redis_con = redis.Redis(host=redis_host, port=redis_port, db=0)
            # 刷新redis库
            self.redis_con.flushdb()
            self.movie_spider_log.info('Redis初始化成功')
        except Exception as err:
            self.movie_spider_log.error('Redis初始化失败' + str(err))

        # 初始化读取ua
        try:
            ua_list_file_path = 'ua_list.txt'
            self.ua_list = []
            with open(ua_list_file_path, 'r') as f:
                line = f.readline()
                while line:
                    self.ua_list.append(line.strip('\n'))
                    line = f.readline()
            self.movie_spider_log.info('UA初始化成功')
        except Exception as err:
            self.movie_spider_log.error('UA初始化失败' + str(err))

        # ip代理
        self.proxies = {"http": "http://10.10.1.10:3128"}
        # 最大待爬取列表数量
        self.max_queue_len = self.config['max_queue_len']
        # 爬虫间隔时间
        self.sleep_time = self.config['sleep_time']
        # 请求时间
        self.timeout = self.config['timeout']

        self.movie_spider_log.info('DouBan-Movie-Spider初始化成功')
    
    def _get_all_movie_id(self):
        # 多线程
        api = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=0'
        pass


    def run(self):
        # 获取电影, 电视剧, 综艺, 动漫, 纪录片, 短片ID
        self._get_all_movie_id()

        # 获取电影, 电视剧, 综艺, 动漫, 纪录片, 短片信息
        pass


if __name__ == '__main__':
    spider = DouBanMovieSpider()
    spider.run()
