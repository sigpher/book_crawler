import json
from os import makedirs
from os.path import exists
import requests
import logging
import re
from urllib.parse import urljoin
import multiprocessing

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

BASE_URL = 'https://books.toscrape.com'
TOTAL_PAGE = 50

RESULTS_DIR = 'results'
exists(RESULTS_DIR) or makedirs((RESULTS_DIR))


def scrape_page(url):
    logging.info('scraping page %s...', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        logging.error(
            'get invalid status code: %s\t while scraping %s', response.status_code, url)

    except requests.RequestException:
        logging.error('error occurred while scraping %s', url, exc_info=True)


def scrape_index(page):
    """
    爬取一个页面,返回detail页面html
    :param url:详情页url
    :return:详情页html
    """
    index_url = f'{BASE_URL}/catalogue/page-{page}.html'
    return scrape_page(index_url)


def parse_index(html):
    index_pattern = re.compile('<h3><a href="(.*?\.html)"')
    items = re.findall(index_pattern, html)
    if not items:
        return []
    for item in items:
        reletive_url = f'/catalogue/{item}'
        detail_url = urljoin(BASE_URL, reletive_url)
        logging.info('get detail url %s', detail_url)
        yield detail_url


def scrape_detail(url):
    """
    scrape detail page and return its html
    :param page: page of detail page
    :return: html of detail page
    """
    return scrape_page(url)


def parse_detail(html):
    """
    爬取一个页面,返回detail页面html
    :param html:详情页html
    :return:详情页html
    """
    title_pattern = re.compile('<h1>(.*?)</h1>')
    upc_pattern = re.compile('<th>UPC</th><td>(.*?)</td>')
    price_pattern = re.compile('<p class="price_color">.(.*?)</p>')
    available_parttern = re.compile('<td>In stock \((.*?) available\)</td>')
    thumbnail_parttern = re.compile('<img\s*src="(.*?)"*/>')
    desc_parttern = re.compile('<p>(.*?)</p>')

    title = re.search(title_pattern, html).group(
        1).strip() if re.search(title_pattern, html) else None
    upc = re.search(upc_pattern, html).group(
        1).strip() if re.search(upc_pattern, html) else None
    price = re.search(price_pattern, html).group(
        1).strip() if re.search(price_pattern, html) else None
    avaliable = re.search(available_parttern, html).group(
        1).strip() if re.search(available_parttern, html) else None
    thumbnail = re.search(thumbnail_parttern, html).group(
        1).strip() if re.search(thumbnail_parttern, html) else None
    desc = re.search(desc_parttern, html).group(
        1).strip() if re.search(desc_parttern, html) else None
    return {'title': title, 'upc': upc, 'price': price, 'thumbnail': thumbnail, 'avaliable': avaliable, 'desc': desc}


def clean_title(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title


def save_data(data):
    """
    保存到json文件
    :param data: JSON data
    :return:
    """
    title = clean_title(data.get('title'))
    data_path = f'{RESULTS_DIR}/{title}.json'
    json.dump(data, open(data_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


# def main():
#     for page in range(1, TOTAL_PAGE+1):
#         index_html = scrape_index(page)
#         detail_urls = parse_index(index_html)
#         for detail_url in detail_urls:
#             detail_html = scrape_detail(detail_url)
#             data = parse_detail(detail_html)
#             # logging.info('get detail data %s', data)
#             logging.info('saving data to json file')
#             save_data(data)
#             logging.info('data saved successfully')


# if __name__ == '__main__':
#     main()


# 多线程爬虫
def main(page):
    index_html = scrape_index(page)
    detail_urls = parse_index(index_html)
    for detail_url in detail_urls:
        detail_html = scrape_detail(detail_url)
        data = parse_detail(detail_html)
        logging.info('get detail data %s', data)
        logging.info('saving data to json file')
        save_data(data)
        logging.info('data saved successfully')


if __name__ == '__main__':
    pool = multiprocessing.Pool()
    pages = range(1, TOTAL_PAGE+1)
    pool.map(main, pages)
    pool.close()
    pool.join()
