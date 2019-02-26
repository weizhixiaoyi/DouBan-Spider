# -*- coding: utf-8 -*-

from movie.movie_crawl import DouBanMovieSpider
from book.book_crawl import DouBanBookSpider


def run():
    """
    获取豆瓣电影和书籍信息
    :return:
    """
    # 获取电影信息
    movie_crawl = DouBanMovieSpider()
    movie_crawl.run()
    # 获取书籍信息
    book_crawl = DouBanBookSpider()
    book_crawl.run()


if __name__ == '__main__':
    run()
