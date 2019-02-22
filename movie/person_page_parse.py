# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup


class PersonPageParse:
    def __init__(self, person_id, person_info_html):
        """
        初始化
        :param person_id:
        :param person_info_html:
        """
        self.person_id = person_id
        self.person_info_html = person_info_html
        self.person_soup = BeautifulSoup(self.person_info_html, 'lxml')

    def _get_person_name(self):
        """
        获取演员姓名
        :return:
        """
        try:
            content_str = str(self.person_soup.find('div', id='content'))
            # print(content_str)
            name_str = re.search(r'<h1>.*</h1>', content_str).group()
            name = name_str.replace('<h1>', '').replace('</h1>', '')
        except Exception as err:
            name = ''
        return name

    def _get_person_gender(self):
        """
        获取演员性别
        :return:
        """
        try:
            gender = 'None'
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '性别' in line:
                    gender_str = str(re.search(r'性别</span>:.*</li>', line).group())
                    gender = gender_str.replace('性别</span>:', '').replace('</li>', '')
        except Exception as err:
            gender = 'None'
        return gender

    def parse(self):
        """
        获取演员信息
        :return:
        """
        name = self._get_person_name()  # 演员姓名
        gender = self._get_person_gender()  # 演员性别

        person_info_json = {
            'name': name,
            'gender': gender
        }
        print(person_info_json)


if __name__ == '__main__':
    person_id = '/celebrity/1276086/'
    person_url = 'https://movie.douban.com' + str(person_id)
    person_info_html = requests.get(person_url).text
    person_page_parse = PersonPageParse(person_id, person_info_html)
    person_page_parse.parse()
