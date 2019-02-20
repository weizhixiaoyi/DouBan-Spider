import requests
import logging
import logging.config
import yaml
import json
import redis
from multiprocessing.dummy import Pool as ThreadPool
import threading
import math
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

        # 初始化文件
        try:
            movie_info_file_path = '../data/movie_info.txt'
            if os.path.exists(movie_info_file_path):
                os.remove(movie_info_file_path)
            self.movie_spider_log.info('文件初始化成功')
        except Exception as err:
            self.movie_spider_log.info('文件初始化失败' + str(err))

        # ip代理
        self.proxies = {"http": "http://10.10.1.10:3128"}
        # 最大待爬取列表数量
        self.max_queue_len = self.config['max_queue_len']
        # 爬虫间隔时间
        self.sleep_time = self.config['sleep_time']
        # 请求时间
        self.timeout = self.config['timeout']

        self.movie_spider_log.info('DouBan-Movie-Spider初始化成功')

    def _get_movie_id(self, start=0):
        """
        根据api获取电影ID
        :param start:
        :return:
        """
        self.movie_spider_log.info('尝试获取' + str(start) + '页电影ID')
        # 获取电影ID
        try:
            movie_id_api = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=电影&start=' + str(
                start)
            movie_id_text = requests.get(movie_id_api, headers=self.headers, proxies=self.proxies, timeout=self.timeout)
            movie_id_json = json.loads(movie_id_text)
            movie_id_data = movie_id_json['data']
            if len(movie_id_data) == 0:
                self.movie_spider_log.info('获取' + str(start) + '页电影ID成功, 长度为0')
                return None
            else:
                movie_id_list = []
                for movie in movie_id_data:
                    movie_id_list.append(movie['id'])
                self.movie_spider_log.info('获取' + str(start) + '页电影ID成功, 长度为' + str(len(movie_id_list)))
                return movie_id_list
        except Exception as err:
            self.movie_spider_log.info('获取' + str(start) + '页电影ID失败' + str(err))

    def _get_movie_info(self, movie_id):
        """
        获取当前电影信息
        :param movie_id:
        :return:
        """
        self.movie_spider_log.info('尝试获取' + str(movie_id) + '电影信息')
        movie_info_url = 'https://movie.douban.com/subject/' + str(movie_id)
        try:
            movie_info_html = requests.get(movie_info_url, headers=self.headers, proxies=self.proxies,
                                           timeout=self.timeout)

            movie_info = {}

            # 写入到文件之中
            movie_info_file_path = 'movie_info.txt'
            with open(movie_info_file_path, 'a+') as f:
                movie_info_str = json.loads(movie_info)
                f.write(json.dumps(movie_info_str))
        except Exception as err:
            self.movie_spider_log.info('获取' + str(movie_id) + '电影信息失败' + str(err))

    def _get_all_movie_info(self):
        is_end = False
        start = 0
        while not is_end:
            # 获取电影ID
            movie_id_list = self._get_movie_id(start)
            if movie_id_list is None:
                break

            # 多线程获取电影Info
            pool = ThreadPool(8)
            pool.map(self._get_movie_info, movie_id_list)
            pool.close()
            pool.join()

    def run(self):
        """
        获取电影信息和电影演员信息
        :return:
        """
        # 获取电影信息
        self._get_all_movie_info()


if __name__ == '__main__':
    spider = DouBanMovieSpider()
    spider.run()
