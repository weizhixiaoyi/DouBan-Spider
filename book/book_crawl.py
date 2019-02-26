# -*- coding: utf-8 -*-

import requests
import logging
import logging.config
import yaml
import re
import json
import redis
from multiprocessing.dummy import Pool as ThreadPool
from bs4 import BeautifulSoup
from book_page_parse import BookPageParse
from book_person_page_parse import PersonPageParse
import time
import random
import os


class DouBanBookSpider:
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
            'Host': 'book.douban.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }

        # 初始化log
        try:
            log_config_file_path = '../log/book_log_config.yaml'
            with open(log_config_file_path, 'r') as f:
                log_config = yaml.load(f)
                logging.config.dictConfig(log_config)
            self.book_spider_log = logging.getLogger('spider')
            self.book_spider_log.info('Logger初始化成功')
        except Exception as err:
            print('Logger初始化失败' + str(err))

        # 初始化配置
        try:
            spider_cofig_file_path = 'book_spider_config.yaml'
            with open(spider_cofig_file_path, 'r') as f:
                spider_config = yaml.load(f)
                self.config = spider_config
                self.book_spider_log.info('Config初始化成功')
        except Exception as err:
            self.book_spider_log.error('Config初始化失败' + str(err))

        # 初始化redis
        try:
            redis_host = self.config['redis']['host']
            redis_port = self.config['redis']['port']
            self.redis_con = redis.Redis(host=redis_host, port=redis_port, db=0)
            # 刷新redis库
            self.redis_con.flushdb()
            self.book_spider_log.info('Redis初始化成功')
        except Exception as err:
            self.book_spider_log.error('Redis初始化失败' + str(err))

        # 初始化读取ua
        try:
            ua_list_file_path = '../proxy/ua_list.txt'
            self.ua_list = []
            with open(ua_list_file_path, 'r') as f:
                line = f.readline()
                while line:
                    self.ua_list.append(line.strip('\n'))
                    line = f.readline()
            self.book_spider_log.info('UA初始化成功')
        except Exception as err:
            self.book_spider_log.error('UA初始化失败' + str(err))

        # 初始化文件
        try:
            book_info_file_path = '../data/book_info.txt'
            if os.path.exists(book_info_file_path):
                os.remove(book_info_file_path)
            person_info_file_path = '../data/book_person_info.txt'
            if os.path.exists(person_info_file_path):
                os.remove(person_info_file_path)
            self.book_spider_log.info('文件初始化成功')
        except Exception as err:
            self.book_spider_log.info('文件初始化失败' + str(err))

        # ip代理
        self.proxies = {"http": "http://10.10.1.10:3128"}
        # 请求过期时间
        self.timeout = self.config['timeout']

        self.book_spider_log.info('DouBan-Book-Spider初始化成功')

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
        self.book_spider_log.info('当前ua为' + str(self.ua_list[rand]))

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
            self.book_spider_log.info('检查ip' + str(check_ip_proxies) + '可行性...')
            try:
                rand_url = self._set_random_test_url()
                check_ip_response = requests.get(rand_url, proxies=check_ip_proxies, timeout=5)
                check_ip_status = check_ip_response.status_code
                if check_ip_status == 200:
                    self.proxies.clear()
                    self.proxies['https'] = rand_ip.strip('\n')
                    self.book_spider_log.info('当前ip' + str(check_ip_proxies) + '可行')
                    self.book_spider_log.info('当前ip设置为' + str(self.proxies))
                    ip_flag = True
                else:
                    self.book_spider_log.info('当前ip' + str(check_ip_proxies) + '不可行, 尝试其他中...')
            except Exception as err:
                self.book_spider_log.error('当前ip' + str(check_ip_proxies) + '不可行, 尝试其他中...' + str(err))

    def get_book_tags(self):
        """
        得到所有书籍标签
        :return:
        """
        self.book_spider_log.info('尝试获取书籍标签信息中...')
        try:
            self._set_random_ua()
            self._set_random_ip()
            # self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            tags_url = 'https://book.douban.com/tag/?view=type'
            tags_response = requests.get(tags_url, headers=self.headers, proxies=self.proxies, timeout=self.timeout)
            tags_html = tags_response.text

            # parse html
            tags_list = []
            tags_soup = BeautifulSoup(tags_html, 'lxml')
            tags_table = str(tags_soup.find('div', class_='article'))
            tags_table_list = tags_table.split('\n')
            for line in tags_table_list:
                if 'href="/tag/' in line:
                    tag = str(re.sub('<td.*">', '', line))
                    tag = re.sub('<.*>', '', tag)
                    tags_list.append(tag)

            self.book_spider_log.info('获取书籍标签信息成功, 内容为' + str(tags_list))
            return tags_list
        except Exception as err:
            self.book_spider_log.error('获取书籍标签信息失败' + str(err))

    def get_book_id(self, book_tag='小说', start=0):
        """
        获取当前页面的书籍ID
        :param book_tag:
        :param start:
        :return:
        """
        self.book_spider_log.info('尝试获取' + str(book_tag) + 'tag, 第' + str(start) + '个书籍ID')
        try:
            self._set_random_ua()
            self._set_random_ip()
            # self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            book_tag_url = 'https://book.douban.com/tag/' + str(book_tag) + '?start=' + str(start) + '&type=T'
            book_tag_page_response = requests.get(book_tag_url, headers=self.headers, proxies=self.proxies,
                                                  timeout=self.timeout)
            book_tag_page_html = book_tag_page_response.text
            if '没有找到符合条件的图书' in book_tag_page_html:
                self.book_spider_log.info('获取' + str(book_tag) + 'tag, 没有找到符合条件的图书')
                return None
            else:
                book_id_list = []
                book_tag_page_soup = BeautifulSoup(book_tag_page_html, 'lxml')
                book_subject_list = book_tag_page_soup.find_all('a', class_='nbg')
                for book in book_subject_list:
                    id_str_list = re.findall(r'subject_id:\'.*\',', str(book))
                    if id_str_list:
                        book_id = str(id_str_list[0]).replace('\'', '').replace('subject_id:', '').replace(',', '')
                        book_id_list.append(book_id)

                self.book_spider_log.info('尝试获取' + str(book_tag) + 'tag, 第' + str(start) + '个书籍ID成功')
                if book_id_list:
                    return book_id_list
                else:
                    return None
        except Exception as err:
            self.book_spider_log.info('尝试获取' + str(book_tag) + 'tag, 第' + str(start) + '个书籍ID失败' + str(err))
            return None

    def _add_wait_author(self, person_href):
        """
        加入待抓取演员队列
        :param user_token:
        :return:
        """
        try:
            if not self.redis_con.hexists('already_get_author', person_href):
                self.redis_con.hset('already_get_author', person_href, 1)
                self.redis_con.lpush('author_queue', person_href)
                self.book_spider_log.info('添加作者' + str(person_href) + '到待爬取队列成功')
        except Exception as err:
            self.book_spider_log.error('添加作者到待爬取队列失败' + str(err))

    def get_book_info(self, book_id):
        """
        获取当前书籍信息
        :return:
        """
        self.book_spider_log.info('开始获取书籍' + str(book_id) + '信息...')
        try:
            self._set_random_ua()
            self._set_random_ip()
            self._set_random_sleep_time()
            time.sleep(self.sleep_time)

            book_info_url = 'https://book.douban.com/subject/' + str(book_id)
            book_info_response = requests.get(book_info_url, headers=self.headers, proxies=self.proxies,
                                              timeout=self.timeout)
            book_info_html = book_info_response.text
            book_page_parse = BookPageParse(book_id, book_info_html)
            book_info_json = book_page_parse.parse()
            self.book_spider_log.info('获取书籍' + str(book_id) + '信息成功')
            self.book_spider_log.info('电影' + str(book_id) + '信息为' + str(book_info_json))

            # 将作者ID加入到redis之中
            self.book_spider_log.info('添加作者信息到redis之中...')
            key_value = ['author', 'translator']
            for key in key_value:
                for person in book_info_json[key]:
                    if person['href']:
                        self._add_wait_author(person['href'])

            # 将电影信息保存到文件之中
            self.book_spider_log.info('保存书籍' + str(book_id) + '信息到文件之中...')
            book_info_file_path = '../data/book_info.txt'
            with open(book_info_file_path, 'a+') as f:
                f.write(json.dumps(book_info_json, ensure_ascii=False) + '\n')
        except Exception as err:
            self.book_spider_log.error('获取书籍' + str(book_id) + '信息失败' + str(err))

    def get_person_info(self, person_id):
        """
        得到作者信息
        :return:
        """
        self.book_spider_log.info('开始获取作者' + str(person_id) + '信息...')
        try:
            self._set_random_ua()
            self._set_random_ip()
            self._set_random_sleep_time()
            # time.sleep(self.sleep_time)
            person_info_html = requests.get(person_id, headers=self.headers, proxies=self.proxies,
                                            timeout=self.timeout).text
            person_page_parse = PersonPageParse(person_id, person_info_html)
            person_info_json = person_page_parse.parse()
            self.book_spider_log.info('获取作者' + str(person_id) + '信息成功')
            self.book_spider_log.info('作者' + str(person_id) + '信息为' + str(person_info_json))

            # 将演员信息保存到文件之中
            self.book_spider_log.info('保存作者' + str(person_id) + '信息到文件之中')
            person_info_file_path = '../data/book_person_info.txt'
            with open(person_info_file_path, 'a+') as f:
                f.write(json.dumps(person_info_json, ensure_ascii=False) + '\n')
        except Exception as err:
            self.book_spider_log.error('获取演员' + str(person_id) + '信息失败')

    def get_all_book_info(self):
        """
        迭代爬取所有种类书籍信息和作者信息
        :return:
        """
        # 得到书籍标签信息
        book_tags = self.get_book_tags()
        for tag in book_tags:
            is_end = False
            start = 0
            while not is_end:
                # 获取书籍ID
                book_id_list = self.get_book_id(tag, start)
                if not book_id_list and start <= 9800:
                    # 如果小于9000, 而且是空, 再尝试访问5次
                    for i in range(0, 3):
                        book_id_list = self.get_book_id(tag, start)
                        if book_id_list:
                            self.book_spider_log.info(
                                '尝试获取' + str(tag) + 'type, 第' + str(start) + '个书籍ID失败, 重试第' + str(i) + '次数成功')
                            break
                        else:
                            self.book_spider_log.info(
                                '尝试获取' + str(tag) + 'type, 第' + str(start) + '个书籍ID失败, 重试第' + str(i) + '次数失败')
                        time.sleep(10)
                elif not book_id_list:
                    break

                # 多线程获取书籍Info
                movie_pool = ThreadPool(12)
                movie_pool.map(self.get_book_info, book_id_list)
                movie_pool.close()
                movie_pool.join()

                # 多线程获取电影演员信息
                person_id_list = []
                while self.redis_con.llen('author_queue'):
                    # 出队列获取演员ID
                    person_id_list.append(str(self.redis_con.rpop('author_queue').decode('utf-8')))
                author_poll = ThreadPool(12)
                author_poll.map(self.get_person_info, person_id_list)
                author_poll.close()
                author_poll.join()

                # 进行下一轮迭代
                start += 20

    def run(self):
        """
        获取书籍信息和书籍作者信息
        :return:
        """
        # 获取书籍信息
        self.get_all_book_info()


if __name__ == '__main__':
    dou_ban_book_spider = DouBanBookSpider()
    dou_ban_book_spider.run()
