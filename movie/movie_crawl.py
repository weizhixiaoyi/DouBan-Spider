import requests
import logging
import logging.config
import yaml
import json
import redis
from multiprocessing.dummy import Pool as ThreadPool
from movie_page_parse import MoviePageParse
from person_page_parse import PersonPageParse
import time
import random
import os


class DouBanMovieSpider:
    def __init__(self):
        """
        爬虫初始化
        :param token: init user
        """

        # 请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh,en;q=0.9,zh-CN;q=0.8,en-US;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
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
            ua_list_file_path = '../proxy/ua_list.txt'
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
            person_info_file_path = '../data/movie_person_info.txt'
            if os.path.exists(person_info_file_path):
                os.remove(person_info_file_path)
            self.movie_spider_log.info('文件初始化成功')
        except Exception as err:
            self.movie_spider_log.info('文件初始化失败' + str(err))

        # ip代理
        self.proxies = {"http": "http://10.10.1.10:3128"}
        # 请求过期时间
        self.timeout = self.config['timeout']
        # 电影类型
        self.genres = self.config['genres']

        self.movie_spider_log.info('DouBan-Movie-Spider初始化成功')

    def _set_random_sleep_time(self):
        """
        设置随机睡眠时间
        :return:
        """
        # 爬虫间隔时间
        self.sleep_time = random.randint(1, 2)

    def _set_random_ua(self):
        """
        设置随机ua
        :return:
        """
        ua_len = len(self.ua_list)
        rand = random.randint(0, ua_len - 1)
        self.headers['User-Agent'] = self.ua_list[rand]
        self.movie_spider_log.info('当前ua为' + str(self.ua_list[rand]))

    @staticmethod
    def _read_ip_list():
        """
        读取ip文件
        :return:
        """
        ip_list_file_path = '../proxy/ip_list.txt'
        ip_list = []
        with open(ip_list_file_path, 'r') as f:
            line = f.readline()
            while line:
                ip_list.append(line)
                line = f.readline()
        return ip_list

    @staticmethod
    def _set_random_test_url():
        """
        随机生成测试url
        :return:
        """
        test_url_list = ['https://www.baidu.com/', 'https://www.sogou.com/', 'http://soso.com/', 'https://www.so.com/']
        rand = random.randint(0, len(test_url_list) - 1)
        rand_url = test_url_list[rand]
        return rand_url

    def _set_random_ip(self):
        """
        设置随机ip, 并检查可用性
        :return:
        """
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
                rand_url = self._set_random_test_url()
                check_ip_response = requests.get(rand_url, proxies=check_ip_proxies, timeout=5)
                check_ip_status = check_ip_response.status_code
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

    def _is_parse_movie_id(self, movie_id):
        """
        判断是否已经爬取过该id
        :return:
        """
        try:
            if self.redis_con.hexists('already_parse_movie', movie_id):
                self.movie_spider_log.info('已经解析过' + str(movie_id) + '电影')
                return True
            else:
                self.redis_con.hset('already_parse_movie', movie_id, 1)
                self.movie_spider_log.info('没有解析过' + str(movie_id) + '电影, 等待解析')
                return False
        except Exception as err:
            return False

    def get_movie_id(self, movie_type='', start=0):
        """
        根据api获取电影ID
        :param start:
        :return:
        """
        self.movie_spider_log.info('尝试获取' + str(movie_type) + 'type, 第' + str(start) + '个电影ID')
        # 获取电影ID
        try:
            self._set_random_ua()
            self._set_random_ip()
            # self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            movie_id_api = 'https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=' + str(
                start) + '&genres=' + str(movie_type)
            movie_id_text = requests.get(movie_id_api, headers=self.headers, proxies=self.proxies,
                                         timeout=self.timeout).text
            movie_id_json = json.loads(movie_id_text)
            movie_id_data = movie_id_json['data']
            if len(movie_id_data) == 0:
                self.movie_spider_log.error('获取' + str(movie_type) + 'type, 第' + str(start) + '个电影ID失败, 长度为0')
                return None
            else:
                movie_id_list = []
                for movie in movie_id_data:
                    if self._is_parse_movie_id(movie['id']):
                        continue
                    else:
                        movie_id_list.append(movie['id'])
                self.movie_spider_log.info(
                    '获取' + str(movie_type) + 'type, 第' + str(start) + '个电影ID成功, 长度为' + str(len(movie_id_list)))
                return movie_id_list
        except Exception as err:
            self.movie_spider_log.info('获取' + str(movie_type) + 'type, 第' + str(start) + '个电影ID失败' + str(err))
            return None

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

    def get_movie_info(self, movie_id):
        """
        获取当前电影信息
        :param movie_id:
        :return:
        """
        self.movie_spider_log.info('开始获取电影' + str(movie_id) + '信息...')
        try:
            self._set_random_ua()
            self._set_random_ip()
            # self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            movie_url = 'https://movie.douban.com/subject/' + str(movie_id) + '/'
            movie_info_response = requests.get(movie_url, headers=self.headers, proxies=self.proxies,
                                               timeout=self.timeout)
            movie_info_html = movie_info_response.text
            movie_page_parse = MoviePageParse(movie_id, movie_info_html)
            movie_info_json = movie_page_parse.parse()
            self.movie_spider_log.info('获取电影' + str(movie_id) + '信息成功')
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

    def get_person_info(self, person_id):
        """
        获取演员信息
        :param actor_id:
        :return:
        """
        self.movie_spider_log.info('开始获取演员' + str(person_id) + '信息...')
        try:
            self._set_random_ua()
            self._set_random_ip()
            self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            person_url = 'https://movie.douban.com' + str(person_id)
            person_info_html = requests.get(person_url, headers=self.headers, proxies=self.proxies,
                                            timeout=self.timeout).text
            person_page_parse = PersonPageParse(person_id, person_info_html)
            person_info_json = person_page_parse.parse()
            self.movie_spider_log.info('获取演员' + str(person_id) + '信息成功')
            self.movie_spider_log.info('演员' + str(person_id) + '信息为' + str(person_info_json))

            # 将演员信息保存到文件之中
            self.movie_spider_log.info('保存演员' + str(person_id) + '信息到文件之中')
            person_info_file_path = '../data/movie_person_info.txt'
            with open(person_info_file_path, 'a+') as f:
                f.write(json.dumps(person_info_json, ensure_ascii=False) + '\n')
            time.sleep(self.sleep_time)

        except Exception as err:
            self.movie_spider_log.error('获取演员' + str(person_id) + '信息失败')

    def get_all_movie_info(self):
        """
        迭代爬取所有种类电影信息和演员信息
        :return:
        """
        for movie_type in self.genres:
            is_end = False
            start = 0
            while not is_end:
                # 获取电影ID
                movie_id_list = self.get_movie_id(movie_type, start)
                if not movie_id_list:
                    break

                # 多线程获取电影Info
                movie_pool = ThreadPool(12)
                movie_pool.map(self.get_movie_info, movie_id_list)
                movie_pool.close()
                movie_pool.join()

                # 多线程获取电影演员信息
                person_id_list = []
                while self.redis_con.llen('actor_queue'):
                    # 出队列获取演员ID
                    person_id_list.append(str(self.redis_con.rpop('actor_queue').decode('utf-8')))
                actor_pool = ThreadPool(12)
                actor_pool.map(self.get_person_info, person_id_list)
                actor_pool.close()
                actor_pool.join()

                # 进行下一轮迭代
                start += 20

    def run(self):
        """
        获取电影信息和电影演员信息
        :return:
        """
        # 获取电影信息
        self.get_all_movie_info()


if __name__ == '__main__':
    spider = DouBanMovieSpider()
    spider.run()
