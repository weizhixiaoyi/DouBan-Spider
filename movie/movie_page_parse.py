# -*- coding: utf-8 -*-


class MoviePageParse:
    def __init__(self, movie_id):
        self.movie_id = movie_id
        self.movie_url = 'https://movie.douban.com/subject/' + str(movie_id)

    def parse(self):
        self.movie_spider_log.info('尝试获取' + str(movie_id) + '电影信息...')
        movie_info_url = 'https://movie.douban.com/subject/' + str(movie_id)
        try:
            movie_info_html = requests.get(movie_info_url, headers=self.headers, proxies=self.proxies,
                                           timeout=self.timeout)
            movie_tree = etree.HTML(movie_info_html)

            # 解析电影页面获取电影信息
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
            summary = movie_tree.xpath('//*[@id="link-report"]/span[1]')[0].text.replace(' ', '').replace('\u3000',
                                                                                                          '').replace(
                '\n', '')
            # 电影平均评分
            average = movie_tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/strong')[0].text
            # 电影总评价人数
            reviews_count = movie_tree.xpath('//*[@id="interest_sectl"]/div[1]/div[2]/div/div[2]/a/span')[0].text
            # 电影评分信息
            rating = {
                'average': average,
                'reviews_count': reviews_count
            }

            movie_info_json = {
                'id': movie_id,
                'name': name,
                'director': directors,
                'writers': writers,
                'casts': casts,
                'genres': genres,
                'countries': countries,
                'language': language,
                'release_data': release_date,
                'durations': durations,
                'other_name': other_name,
                'summary': summary,
                'rating': rating
            }
            self.movie_spider_log.info('获取电影' + str(movie_id) + '信息成功')
            self.movie_spider_log.info('电影' + str(movie_id) + '信息为' + str(movie_info_json))

            # 将演员ID加入到待抓取队列
            self._add_wait_actor(movie_info_json)

            # 将演员信息写入到文件之中
            self._save_movie_info(movie_info_json)
        except Exception as err:
            self.movie_spider_log.info('获取电影' + str(movie_id) + '信息失败' + str(err))
