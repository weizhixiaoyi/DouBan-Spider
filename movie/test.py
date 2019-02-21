import requests
from lxml import etree
import json
from bs4 import BeautifulSoup


def parse_movie():
    movie_url = 'https://movie.douban.com/subject/1438689/'
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
    for text in temp_text:
        if text[0] == '/':
            temp_text.remove(text)

    # 电影制片国家/地区
    countries = temp_text[0]
    # 电影语言
    language = temp_text[1]
    # 电影其他名称
    other_name = temp_text[-1]
    # 电影上映日期
    release_date = movie_tree.xpath('//*[@id="info"]/span[10]')[0].text
    # 电影片长
    durations = movie_tree.xpath('//*[@id="info"]/span[12]')[0].text
    # 电影简介
    print(movie_tree.xpath('//*[@id="link-report"]/span/text()'))
    summary = movie_tree.xpath('//*[@id="link-report"]/span')[0].text.replace(' ', '').replace('\u3000', '').replace(
        '\n', '')
    # 电影评分
    # 平均得分
    average = movie_tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/strong')[0].text
    # 评价人数
    reviews_count = movie_tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/div/div[2]/a/span')[0].text
    rating = {
        'average': average,
        'reviews_count': reviews_count
    }

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
        'summary': summary,
        'rating': rating
    }
    print(movie_info_json)
    movie_info_file_path = '../data/movie_info.txt'
    with open(movie_info_file_path, 'w') as f:
        f.write(json.dumps(movie_info_json, ensure_ascii=False))

def parse_actor():
    actor_url = 'https://movie.douban.com/celebrity/1276086/'
    actor_info_html = requests.get(actor_url).text
    actor_tree = etree.HTML(actor_info_html)

    # 获取演员信息
    # 演员姓名
    name = actor_tree.xpath('//*[@id="content"]/h1')[0].text
    # 演员性别
    gender = actor_tree.xpath('//*[@id="headline"]/div[2]/ul/li[1]')[0].text

    actor_info_json = {
        'name': name,
        'gender': gender
    }
    print(actor_info_json)



if __name__ == '__main__':
    parse_movie()
    # parse_actor()
