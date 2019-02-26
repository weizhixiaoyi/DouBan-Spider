# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup


class PersonPageParse:
    def __init__(self, person_id, person_info_html):
        """
        初始化
        :param person_url:
        :param person_info_html:
        """
        self.person_id = person_id
        self.person_info_html = person_info_html
        self.person_soup = BeautifulSoup(self.person_info_html, 'lxml')

    def _get_person_name(self):
        """
        得到作者名称
        :return:
        """
        try:
            content_str = str(self.person_soup.find('div', id='content'))
            name_str = str(re.search(r'<h1>.*</h1>', content_str).group())
            name = name_str.replace('<h1>', '').replace('</h1>', '')
        except Exception as err:
            name = ''
        return name

    def _get_person_image_url(self):
        """
        得到作者图片链接
        :return:
        """
        try:
            image_url = str(self.person_soup.find('img', title='点击看大图')['src'])
        except Exception as err:
            image_url = ''
        return image_url

    def _get_person_gender(self):
        """
        得到作者性别
        :return:
        """
        try:
            gender = ''
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '性别' in line:
                    gender_str = str(re.search(r'性别</span>:.*</li>', line).group())
                    gender = gender_str.replace('性别</span>:', '').replace('</li>', '')
                    break
        except Exception as err:
            gender = ''
        return gender

    def parse(self):
        """
        获取作者信息
        :return:
        """
        name = self._get_person_name()  # 作者名称
        image_url = self._get_person_image_url()  # 作者图片链接
        gender = self._get_person_gender()  # 作者性别

        person_info_json = {
            'id': self.person_id,
            'name': name,
            'image_url': image_url,
            'gender': gender
        }
        print(person_info_json)
        return person_info_json


if __name__ == '__main__':
    person_id = '4537266'
    person_url = 'https://book.douban.com/author/' + str(person_id)
    person_info_html = requests.get(person_url).text
    person_page_parse = PersonPageParse(person_id, person_info_html)
    person_page_parse.parse()
