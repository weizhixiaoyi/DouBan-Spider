import requests
from lxml import etree


def parse():
    movie_url = 'https://movie.douban.com/subject/26266893/'
    movie_info_text = requests.get(movie_url).text
    movie_tree = etree.HTML(movie_info_text)
    movie_info_json = {}
    movie_info_json['name'] = movie_tree.xpath('//*[@id="content"]/h1/span[1]')[0].text
    movie_info_json['writers'] = [writer.text for writer in movie_tree.xpath('//*[@id="info"]/span[2]/span[2]/a')]
    print(movie_info_json)


if __name__ == '__main__':
    parse()
