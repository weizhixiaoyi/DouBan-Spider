import requests
import logging
import logging.config
import yaml
import json
import redis
from multiprocessing.dummy import Pool as ThreadPool
from movie_page_parse import MoviePageParse
from person_page_parse import PersonPageParse
from lxml import etree
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,en;q=0.9,zh-CN;q=0.8,en-US;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            # 'Cookie': 'bid=WRsiEQh1RCo; douban-fav-remind=1; ll="118254"; __yadk_uid=HQHT9E1iGfMaR80pI7AVEM4vNlkEJ8WA; _vwo_uuid_v2=D9946A908995872216194637C384BD701|b3cfeedd0b220f53ad60e5ddcfa76ea6; gr_user_id=072a583f-245a-4387-8ee8-a45eeb138afd; __utmz=30149280.1550299539.5.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); ct=y; push_doumail_num=0; __utmc=30149280; __utmc=223695111; viewed="25862578_1770782_4908885_26912767_1004821_1099305_2111801_1052241"; __utmv=30149280.15783; push_noty_num=0; __utmz=223695111.1550833472.14.11.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1550907831%2C%22https%3A%2F%2Fwww.douban.com%2F%22%5D; _pk_id.100001.4cf6=c46869fa5b8634cf.1545648265.17.1550907831.1550905349.; _pk_ses.100001.4cf6=*; __utma=30149280.1456284366.1545648198.1550902744.1550907831.22; __utmb=30149280.0.10.1550907831; __utma=223695111.82726815.1545648265.1550902744.1550907831.19; __utmb=223695111.0.10.1550907831; ap_v=0,6.0',
            'Host': 'movie.douban.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
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
            person_info_file_path = '../data/person_info.txt'
            if os.path.exists(person_info_file_path):
                os.remove(person_info_file_path)
            self.movie_spider_log.info('文件初始化成功')
        except Exception as err:
            self.movie_spider_log.info('文件初始化失败' + str(err))

        # ip代理
        self.proxies = {"http": "http://10.10.1.10:3128"}
        # 最大待爬取列表数量
        self.max_queue_len = self.config['max_queue_len']
        # 请求时间
        self.timeout = self.config['timeout']

        self.movie_spider_log.info('DouBan-Movie-Spider初始化成功')

    def _set_random_sleep_time(self):
        # 爬虫间隔时间
        self.sleep_time = random.randint(2, 4)

    def _set_random_ua(self):
        ua_len = len(self.ua_list)
        rand = random.randint(0, ua_len - 1)
        self.headers['User-Agent'] = self.ua_list[rand]
        self.movie_spider_log.info('当前ua为' + str(self.ua_list[rand]))

    @staticmethod
    def _read_ip_list():
        ip_list_file_path = 'ip_list.txt'
        ip_list = []
        with open(ip_list_file_path, 'r') as f:
            line = f.readline()
            while line:
                ip_list.append(line)
                line = f.readline()
        return ip_list

    def _set_random_ip(self):
        ip_flag = False
        while not ip_flag:
            ip_list = self._read_ip_list()
            ip_len = len(ip_list)
            rand = random.randint(0, ip_len - 1)
            rand_ip = ip_list[rand]
            if 'https' in rand_ip:
                check_ip_proxies = {'https': rand_ip.strip('\n')}
            else:
                check_ip_proxies = {'http': rand_ip.strip('\n')}
            self.movie_spider_log.info('检查ip' + str(check_ip_proxies) + '可行性...')
            try:
                check_ip_responce = requests.get('https://www.baidu.com/', proxies=check_ip_proxies,
                                                 timeout=5)
                check_ip_status = check_ip_responce.status_code
                if check_ip_status == 200:
                    self.proxies.clear()
                    self.proxies['https'] = rand_ip.strip('\n')
                    self.movie_spider_log.info('当前ip' + str(check_ip_proxies) + '可行')
                    self.movie_spider_log.info('当前ip设置为' + str(self.proxies))
                    ip_flag = True
                else:
                    self.movie_spider_log.info('当前ip' + str(check_ip_proxies) + '不可行, 尝试其他中...')
            except Exception as err:
                self.movie_spider_log.error('当前ip' + str(check_ip_proxies) + '不可行, 尝试其他中...' + str(err))

    def _get_movie_id(self, start=0):
        """
        根据api获取电影ID
        :param start:
        :return:
        """
        self.movie_spider_log.info('尝试获取' + str(start) + '页电影ID')
        # 获取电影ID
        try:
            self._set_random_sleep_time()
            self._set_random_ua()
            self._set_random_ip()
            movie_id_api = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=' + str(start)
            movie_id_text = requests.get(movie_id_api, headers=self.headers, proxies=self.proxies,
                                         timeout=self.timeout).text
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
            return None

    def _save_movie_info(self, movie_info_json):
        """
        保存电影信息到文件之中
        :param movie_info_json:
        :return:
        """
        movie_info_str = json.dumps(movie_info_json, ensure_ascii=False)
        movie_info_file_path = '../data/movie_info.txt'
        try:
            with open(movie_info_file_path, 'a+') as f:
                f.write(movie_info_str)
            self.movie_spider_log.info('写入电影' + str(movie_info_json['id']) + '到文件成功')
        except Exception as err:
            self.movie_spider_log.error('写入电影' + str(movie_info_json['id']) + '到文件失败' + str(err))

    def _add_wait_actor(self, person_href):
        """
        加入待抓取演员队列
        :param user_token:
        :return:
        """
        try:
            if not self.redis_con.hexists('already_get_actor', person_href):
                self.redis_con.hset('already_get_actor', person_href, 1)
                self.redis_con.lpush('actor_queue', person_href)
                self.movie_spider_log.info('添加演员' + str(person_href) + '到待爬取队列成功')
        except Exception as err:
            self.movie_spider_log.error('添加演员到待爬取队列失败' + str(err))

    def _get_movie_info(self, movie_id):
        """
        获取当前电影信息
        :param movie_id:
        :return:
        """
        self.movie_spider_log.info('开始获取电影' + str(movie_id) + '信息...')
        try:
            self._set_random_sleep_time()
            self._set_random_ua()
            self._set_random_ip()
            time.sleep(self.sleep_time)
            movie_url = 'https://movie.douban.com/subject/' + str(movie_id) + '/'
            movie_info_response = requests.get(movie_url, headers=self.headers, proxies=self.proxies,
                                           timeout=self.timeout)
            movie_info_html = movie_info_response.text
            movie_page_parse = MoviePageParse(movie_id, movie_info_html)
            movie_info_json = movie_page_parse.parse()
            self.movie_spider_log.info('获取电影' + str(movie_id) + '信息成功')
            # self.movie_spider_log.info('电影' + str(movie_id) + '状态码为' + str(movie_info_response.status_code))
            # self.movie_spider_log.info(
            #     '电影' + str(movie_id) + 'HTML为' + str(
            #         movie_info_html.replace('\n', '').replace('\u3000', '').replace(' ', '').replace('\t', '')))
            self.movie_spider_log.info('电影' + str(movie_id) + '信息为' + str(movie_info_json))

            # 将演员ID加入到redis之中
            self.movie_spider_log.info('添加演员信息到redis之中...')
            key_value = ['directors', 'writers', 'actors']
            for key in key_value:
                for person in movie_info_json[key]:
                    if person['href']:
                        self._add_wait_actor(person['href'])

            # 将电影信息保存到文件之中
            self.movie_spider_log.info('保存电影' + str(movie_id) + '信息到文件之中...')
            movie_info_file_path = '../data/movie_info.txt'
            with open(movie_info_file_path, 'a+') as f:
                f.write(json.dumps(movie_info_json, ensure_ascii=False) + '\n')

        except Exception as err:
            self.movie_spider_log.error('获取电影' + str(movie_id) + '信息失败' + str(err))

    def _get_person_info(self, person_id):
        """
        获取演员信息
        :param actor_id:
        :return:
        """
        self.movie_spider_log.info('开始获取演员' + str(person_id) + '信息...')
        try:
            self._set_random_sleep_time()
            # self._set_random_ua()
            self._set_random_ip()
            time.sleep(self.sleep_time)
            person_url = 'https://movie.douban.com' + str(person_id)
            person_info_html = requests.get(person_url, headers=self.headers, proxies=self.proxies,
                                            timeout=self.timeout).text
            person_page_parse = PersonPageParse(person_id, person_info_html)
            person_info_json = person_page_parse.parse()
            self.movie_spider_log.info('获取演员' + str(person_id) + '信息成功')
            self.movie_spider_log.info('演员' + str(person_id) + '信息为' + str(person_info_json))

            # 将演员信息保存到文件之中
            self.movie_spider_log.info('保存演员' + str(person_id) + '信息到文件之中')
            person_info_file_path = '../data/person_info.txt'
            with open(person_info_file_path, 'a+') as f:
                f.write(json.dumps(person_info_json, ensure_ascii=False) + '\n')
            time.sleep(self.sleep_time)

        except Exception as err:
            self.movie_spider_log.error('获取演员' + str(person_id) + '信息失败')

    def _get_all_movie_info(self):
        is_end = False
        start = 0
        while not is_end:
            # 获取电影ID
            movie_id_list = self._get_movie_id(start)
            if (not movie_id_list) and (start <= 9000):
                time.sleep(self.sleep_time)
                continue
            elif not movie_id_list:
                break

            # 多线程获取电影Info
            movie_pool = ThreadPool(12)
            movie_pool.map(self._get_movie_info, movie_id_list)
            movie_pool.close()
            movie_pool.join()

            # 多线程获取电影演员信息
            # person_id_list = []
            # while self.redis_con.llen('actor_queue'):
            #     # 出队列获取演员ID
            #     person_id_list.append(str(self.redis_con.rpop('actor_queue').decode('utf-8')))
            # actor_pool = ThreadPool(12)
            # actor_pool.map(self._get_person_info, person_id_list)
            # actor_pool.close()
            # actor_pool.join()

            # 进行下一轮迭代
            start += 1

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
