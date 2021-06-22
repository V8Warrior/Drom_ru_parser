from bs4 import BeautifulSoup
import requests as req
import numpy as np
import pandas as pd
import re
import json

class drom:

    def __init__(self):
        # Инициализация

        # Cетевые параметры:
        self.urls = dict(host='https://www.drom.ru', cities = "https://auto.drom.ru/cities/", brands = 'https://www.drom.ru/catalog/')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 YaBrowser/21.2.2.102 Yowser/2.5 Safari/537.36',
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }

        # Установка соединения с сайтом
        with req.get(self.urls['host'], headers=self.headers) as r:
            if r.status_code == 200:
                self.html_main = r.text

        # Подключение к Каталогу
        with req.get(self.urls['brands'], headers=self.headers) as r:
            if r.status_code == 200:
                self.html_brands = r.text

        # Подключение к списку Городов
        with req.get(self.urls['cities'], headers=self.headers) as r:
            if r.status_code == 200:
                self.html_cities = r.text

        # Получение данных

        # Марки:
        brands_soup = BeautifulSoup(self.html_brands, 'html.parser') \
            .find('div', class_='css-2u02es ete74kl0') \
            .find_all('a')

        # Города:
        cities_soup = BeautifulSoup(self.html_cities, 'html.parser') \
            .find(class_='b-selectCars b-media-cont') \
            .find_all('a')

        # Атрибуты
        self.brands = (np.array(brands_soup).T)[0]
        self.cities = (np.array(cities_soup).T)[0]

        self.brand = None
        self.models = None
        self.city = None
        self.all_cars = None


    def get_city_link(self, city):
        # Получатель ссылки города
        soup = BeautifulSoup(self.html_cities, 'html.parser') \
            .find(class_='b-selectCars b-media-cont')\
            .find('a', text=city)\
            .get('href')
        return soup

    def get_brand_link(self, brand):
    # Получатель ссылки бренда
        soup = BeautifulSoup(self.html_brands, 'html.parser') \
        .find('div', class_='css-2u02es ete74kl0') \
        .find('a', text=brand) \
        .get('href')
        return soup

    def get_models(self, brand):
        # Получить модели
        url = self.get_brand_link(brand)
        with req.get(url, headers=self.headers) as r:
            if r.status_code == 200:
                html_models = r.text
        soup = BeautifulSoup(html_models, 'html.parser') \
            .find('div', class_='css-2u02es ete74kl0') \
            .get_text("|").split('|')
        models = np.array(soup)
        self.models = models
        return models

    def get_all_cars(self):

        dat = pd.DataFrame([], columns=['model'], index=self.brands)
        dat['model'] = [self.get_models(x) for x in dat.index]
        dat = dat.explode(column='model')
        self.all_cars = dat
        return dat

    def full_link(self, brand='Audi', model='A4', city='Москва'):
        if brand in self.brands:
            brand_link = ''.join(self.get_brand_link(brand).split('/')[4:])

            if city in self.cities:
                city_link = self.get_city_link(city)[:-5]
            else:
                city_link = 'https://auto.drom.ru/'


            if model in self.get_models(brand):
                model = '/' + model.lower()
            else:
                model = ''
        else:
            return 'Некорректное значение'

        link = f'{city_link}{brand_link}{model}/used/'
        return link



drom = drom()

# print(drom.get_city_link('Санкт-Петер'))
# print(drom.get_brand_link('Audi'))
# print(drom.get_models('Audi'))
print(drom.full_link(brand='ГАЗ', model='3110', city='Нижний Новгород'))
print(drom.get_all_cars())


# def get_html(url):
#     with req.get(url, headers=HEADERS) as r:
#         # r.content.decode('utf-8-sig')
#         r.encoding
#     return r
#
# def get_content_stage_1(html):
#     soup = BeautifulSoup(html.text, 'html.parser')
#     # items = soup.find_all('div', class_='css-u4n5gw ebqjjri4')
#     items = soup.find('div', class_='css-2u02es ete74kl0').find_all('noscript' and 'a')
#     # items = find.find_all('a')
#     links = []
#     for item in items:
#         find = item.get('href')
#         if find != []:
#             links.append(find)
#     #     links.append(item.find('a',  class_='css-171rdfx').get('href'))
#     # #     # brands.append(item.find('div', class_='css-1p05nxt').get_text())
#     return links #brands
#
# def get_content_stage_2(html):
#     soup = BeautifulSoup(html.text, 'html.parser')
#     items = soup.find_all('a', class_='e64vuai1')
#     # links = []
#     ends = []
#     # model_names = []
#     for item in items:
#         # links.append(item.get('href'))
#         # model_names.append(item.get_text())
#         ends.append(item.get('href')[28:])
#     return ends #, model_names
#
# def get_content_stage_3(html):
#     soup = BeautifulSoup(html.text, 'html.parser')
#     items = soup.find_all('a', class_='css-1hgk7d1')
#     strings = len(soup.find_all('div', class_='css-12xjs1i e15hqrm30'))
#     cars = []
#     for item in items:
#         cars.append(item.get('href'))
#     return cars
#
# def get_content_stage_4(link):
#     global errlist
#     html = get_html(link)
#     if html.status_code == 200:
#         soup = BeautifulSoup(html.text, 'html.parser')
#         car_data = {}
#         # errlist = []
#         try:
#             fullname = re.findall(r'[/](\w+)',link)
#             # fullname = re.findall(r'\w+', soup.find('h1', class_='css-cgwg2n').get_text()) #css-cgwg2n
#             char_items = soup.find_all('tr', class_='css-10191hq')
#             try:
#                 car_data['name'] = fullname[1]
#                 car_data['model'] = fullname[2]
#             except IndexError:
#                 print(f'Что-то не так с названием, не распределяет по индексам')
#                 errlist.append({'index_err': link})
#
#             for item in char_items:
#                 key = item.find('th', class_='css-k5ermf')
#                 value = item.find('td',class_='css-1uz0iw8 ezjvm5n1')
#                 if key != None and value != None:
#                     car_data[key.get_text()] = value.get_text()
#             try:
#                 car_data['price'] = int(''.join(re.findall(r'\d+', soup.find('div', class_='css-1hu13v1').get_text())))
#                 car_data['link'] = link
#             except AttributeError:
#                 print(f'\nfullname - None (Данные цены не прочитались) in {link}\n')
#                 errlist.append({'price_err': link})
#             return car_data
#         except AttributeError:
#             print(f'\nfullname - None (Данные имени не прочитались) in {link}\n')
#             errlist.append({'nonename' : link})
#             return None
#     else:
#         print(f'Проблема с ссылккой {link}')
#         errlist.append({'connection_problem' : link})
#
#
# def saver(doc, name= ""):
#     with open(f'parsing_data\{name}_drom_ru.json', 'w') as file:
#         json.dump(doc, file)
#
# def error_saver(errlist):
#     with open('parsing_data\err_drom_ru.json', 'w') as file:
#         json.dump(errlist, file)
#
# def parsing_cars(url1, page1=0, page2=1, brandstart=0):
#     global errlist
#     # connect
#     html = get_html(url1)
#     if html.status_code == 200:
#         brandlist = get_content_stage_1(html)
#         # cars = []
#         for brand in brandlist[brandstart:]:
#             html_brand = get_html(brand)
#             if html_brand.status_code == 200:
#                 modellist = get_content_stage_2(html_brand)
#                 brandname = re.findall(r'\w+', brand[28:])[0]
#                 print(brandname)
#                 cars_brand = []
#                 for ends in modellist:
#                     name_model = re.findall(r'\w+', ends)
#                     carurl = 'https://auto.drom.ru/' + ends + 'used/'
#                     print(' '.join(name_model))
#                     for page in range(page1, page2 +1):
#                         url3 = carurl + f'page{page}/'
#                         html_car = get_html(url3)
#                         if html_car.status_code == 200:
#                             print(f'Парсинг страницы: {page}')
#                             carlist = get_content_stage_3(html_car)
#                             if carlist == []:
#                                 print('Данные по модели есть')
#                                 break
#                             for link in carlist:
#                                 print(link)
#                                 car = get_content_stage_4(link)
#                                 if car != None:
#                                     cars_brand.append(car)
#                                     error_saver(errlist)
#                                     # cars.append(car)
#                                 saver(cars_brand, name=brandname)
#                                 # saver(cars, name='all')
#                         else:
#                             print(f'Проблема с ссылккой {url3}')
#                             errlist.append({'connection_problem': url3})
#                             error_saver(errlist)
#             else:
#                 print(f'Проблема с ссылккой {brand}')
#                 errlist.append({'connection_problem': brand})
#                 error_saver(errlist)

# # ТЕСТ
# errlist = []
# par = parsing_cars(URL, 1, 101, -7)

# url1 = 'https://ust-tarka.drom.ru/lada/2121_4x4_niva/41666637.html'
# url2 = 'https://spb.drom.ru/land_rover/range_rover/41748748.html'
# find = get_content_stage_4(url2)
# print(find)