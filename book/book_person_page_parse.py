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

    def _get_person_birthday(self):
        """
        获取作者出生日期
        :return:
        """
        try:
            birthday = ''
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '出生日期' in line:
                    birtyday_str = str(re.search(r'出生日期</span>:.*</li>', line).group())
                    birthday = birtyday_str.replace('出生日期</span>:', '').replace('</li>', '')
                    break
                if '生卒日期' in line:
                    birtyday_str = str(re.search(r'生卒日期</span>:.*</li>', line).group())
                    birthday = birtyday_str.replace('生卒日期</span>:', '').replace('</li>', '')
                    break
        except Exception as err:
            birthday = ''
        return birthday

    def _get_person_country(self):
        """
        获取作者国家/地区
        :return:
        """
        try:
            birthday = ''
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '国家/地区' in line:
                    birtyday_str = str(re.search(r'国家/地区</span>:.*</li>', line).group())
                    birthday = birtyday_str.replace('国家/地区</span>:', '').replace('</li>', '')
                    break
        except Exception as err:
            birthday = ''
        return birthday

    def _get_person_other_chinese_name(self):
        """
        获取作者其他中文名称
        :return:
        """
        try:
            other_chinese_name = ''
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '更多中文名' in line:
                    other_chinese_name_str = str(re.search(r'更多中文名</span>:.*</li>', line).group())
                    other_chinese_name = other_chinese_name_str.replace('更多中文名</span>:', '').replace('</li>', '')
        except Exception as err:
            other_chinese_name = ''
        return other_chinese_name

    def _get_person_other_english_name(self):
        """
        获取作者其他英文名称
        :return:
        """
        try:
            other_english_name = ''
            person_info = BeautifulSoup(str(self.person_soup.find('div', {'class': 'info'})), 'lxml')
            person_info = person_info.find_all('li')
            for line in person_info:
                line = str(line).replace(' ', '').replace('\n', '')
                if '更多外文名' in line:
                    other_english_name_str = str(re.search(r'更多外文名</span>:.*</li>', line).group())
                    other_english_name = other_english_name_str.replace('更多外文名</span>:', '').replace('</li>', '')
        except Exception as err:
            other_english_name = ''
        return other_english_name

    def _get_person_introduction(self):
        """
        获取作者介绍
        :return:
        """
        try:
            introduction = ''
            try:
                # all content
                introduction = str(self.person_soup.find('span', class_='all hidden').text)
                introduction = introduction.replace('\n', '').replace('\u3000', '').replace(' ', '')
            except:
                # short content
                introduction = str(self.person_soup.find_all('div', id='intro')).replace('\n', '')
                introduction = str(re.search('<div class="bd">.*</div>', introduction).group())
                introduction = introduction.replace('<div class="bd">', '').replace('</div>', '').replace('\u3000',
                                                                                                          '').replace(
                    ' ', '')
        except Exception as err:
            introduction = ''
        return introduction

    def parse(self):
        """
        获取作者信息
        :return:
        """
        name = self._get_person_name()  # 作者名称
        image_url = self._get_person_image_url()  # 作者图片链接
        gender = self._get_person_gender()  # 作者性别
        birthday = self._get_person_birthday()  # 作者出生日期
        country = self._get_person_country()  # 作者国家
        other_chinese_name = self._get_person_other_chinese_name()  # 作者其他中文名称
        other_english_name = self._get_person_other_english_name()  # 作者其他英文名称
        introduction = self._get_person_introduction()  # 作者介绍

        person_info_json = {
            'id': self.person_id,
            'name': name,
            'image_url': image_url,
            'gender': gender,
            'birthday': birthday,
            'country': country,
            'other_chinese_name': other_chinese_name,
            'other_english_name': other_english_name,
            'introduction': introduction
        }
        return person_info_json


if __name__ == '__main__':
    person_id = '4502389'
    person_url = 'https://book.douban.com/author/' + str(person_id)
    person_info_html = requests.get(person_url).text
    person_page_parse = PersonPageParse(person_id, person_info_html)
    person_page_parse.parse()
