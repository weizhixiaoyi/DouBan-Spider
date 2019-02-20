import requests
from lxml import etree
import json
from bs4 import BeautifulSoup


def parse():
    movie_url = 'https://movie.douban.com/subject/26266893/'
    movie_info_text = requests.get(movie_url).text
    movie_tree = etree.HTML(movie_info_text)

    # info
    # 电影名称
    name = movie_tree.xpath('//*[@id="content"]/h1/span[1]')[0].text
    # 导演信息
    directors = []
    directors_name = [directors.text for directors in movie_tree.xpath('//*[@id="info"]/span[1]/span[2]/a')]
    director_href = [director for director in movie_tree.xpath('//*[@id="info"]/span[1]/span[2]/a/@href')]
    for i in range(0, len(directors_name)):
        directors.append({'name': directors_name[i], 'href': director_href[i]})
    # 编剧信息
    writers = []
    writers_name = [writers.text for writers in movie_tree.xpath('//*[@id="info"]/span[2]/span[2]/a')]
    writers_href = [writers for writers in movie_tree.xpath('//*[@id="info"]/span[2]/span[2]/a/@href')]
    for i in range(0, len(writers_name)):
        writers.append({'name': writers_name[i], 'href': writers_href[i]})
    # 主演信息
    casts = []
    casts_name = [casts.text for casts in movie_tree.xpath('//*[@id="info"]/span[3]/span[2]/a')]
    casts_href = [casts for casts in movie_tree.xpath('//*[@id="info"]/span[3]/span[2]/a/@href')]
    for i in range(0, len(casts_name)):
        casts.append({'name': casts_name[i], 'href': casts_href[i]})
    # 电影类型
    genres = [genres.text for genres in movie_tree.xpath('//*[@id="info"]/span[@property="v:genre"]')]
    # 制片国家/地区, 语言, 其他名称
    temp_text = [temp.replace('\n', '').replace(' ', '') for temp in
                 movie_tree.xpath('//*[@id="info"]/text()')]
    while '' in temp_text:
        temp_text.remove('')
    while '/' in temp_text:
        temp_text.remove('/')
    # 电影制片国家/地区
    countries = temp_text[0]
    # 电影语言
    language = temp_text[1]
    # 电影其他名称
    other_name = temp_text[2]
    # 电影上映日期
    release_date = movie_tree.xpath('//*[@id="info"]/span[10]')[0].text
    # 电影片长
    durations = movie_tree.xpath('//*[@id="info"]/span[12]')[0].text
    # 电影简介
    summary = movie_tree.xpath('//*[@id="link-report"]/span[1]')[0].text.replace(' ', '').replace('\u3000', '').replace(
        '\n', '')
    # 电影评分
    movie_info_json = {
        'name': name,
        'director': directors,
        'writer': writers,
        'starring': casts,
        'genres': genres,
        'countries': countries,
        'language': language,
        'release_data': release_date,
        'durations': durations,
        'other_name': other_name,
        'summary': summary
    }
    print(movie_info_json)


def parse1():
    movie_url = 'https://movie.douban.com/subject/26266893/'
    movie_info_html = requests.get(movie_url).text
    soup = BeautifulSoup(movie_info_html, 'html.parser')

    # 电影名称
    movie_name = soup.find('span', property="v:itemreviewed").text
    # 电影信息
    movie_info = soup.find_all('div', id='info')
    # print(movie_info)
    for tag in movie_info:
        # 导演信息
        directors_name = tag.find_all('span')[3].find_all['span']
        print(directors_name)

    # print(soup.find('div', id='info'))
    # 导演信息
    # directors = soup.find('span', class_='')

    # print(movie_info_json)


if __name__ == '__main__':
    parse()
    # parse1()
