from bs4 import BeautifulSoup
import requests as req
import numpy as np
import pandas as pd
import os.path as osp
import re
from time import time

class drom:

    def __init__(self):
        # Инициализация

        # Cетевые параметры:
        self.urls = dict(host='https://auto.drom.ru/', cities="https://auto.drom.ru/cities/",
                         brands='https://www.drom.ru/catalog/')
        self.headers = dict(
            User_Agent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.152 YaBrowser/21.2.2.102 Yowser/2.5 Safari/537.36',
            accept='text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        )
        # Соединение
        self.sess = req.session()
        self.sess.headers.update(self.headers)

        # Установка соединения с сайтом
        with self.sess as sess:
            rm, rc = sess.get(self.urls['host'], stream=True), \
                     sess.get(self.urls['cities'], stream=True)
            self.html_main = rm.text if rm.status_code == 200 else None
            self.html_cities = rc.text if rc.status_code == 200 else None

        self.brands = np.array(list(
            map(
                lambda x: [x.getText(), x.get('href')], BeautifulSoup(self.html_main, 'html.parser') \
                    .find('div', class_='css-1xdu4vx ete74kl0') \
                    .find_all('a')))[:-1])
        # Регионы
        self.regions = pd.read_csv('region_data.csv', index_col=0) if osp.exists('region_data.csv') else None
        if self.regions is None:
            print('File with region data not exist, use function: ".get_regions()"')

            # Каталог машин
        self.all_cars = pd.read_csv('all_cars_models.csv', index_col=0) if osp.exists('all_cars_models.csv') else None
        if self.all_cars is None:
            print('File with car data not exist, use function: ".get_cars()"')

        self.linkcount = 0
        self.linkvolume = 0
        self.time = 0
        self.timelists = []
        # Ошибки
        self.errors = []
        self.connection_err = []

    def get_regions(self):
        # Получить кэш регионов
        html = self.html_cities
        dat = pd.DataFrame([], columns=['id', 'region', 'link'])
        soup = BeautifulSoup(html, 'html.parser') \
            .find('div', class_='b-selectCars b-media-cont')
        text = soup.find_all('a', class_='b-link')
        links = soup \
            .find_all('a', class_='b-link', href=True)
        reg_arr = np.array(text)
        link_arr = np.array([link['href'] for link in links])
        dat['link'] = link_arr
        dat['region'] = reg_arr
        dat2 = dat.copy()
        dat2.loc[29, 'link'] = 'https://auto.drom.ru/region77/'
        dat2.loc[63, 'link'] = 'https://auto.drom.ru/region78/'
        reg = lambda x: int(re.findall(r'[0-9]+', x)[0])
        dat2.id = dat2.link.apply(reg)
        dat2.sort_values(by='id', inplace=True)
        dat2.set_index('id', inplace=True)
        dat2.to_csv('region_data.csv')
        self.regions = dat2
        return dat2

    def get_brand_link(self, brand):
        # Получатель ссылки бренда
        link = self.brands[np.argwhere(self.brands == brand)[0][0]][1] if brand in self.brands else None
        return link

    def get_models(self, brand, links=True):
        link = self.get_brand_link(brand)
        unpacker = lambda x: [x.get_text(), x.get('href')]
        with self.sess.get(link, stream=True) as r:
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser') \
                    .find('div', class_="css-1xdu4vx ete74kl0")
                if links:
                    l = soup.find_all('a')
                    models, links = np.array(list(map(unpacker, l))).T
                else:
                    models = np.array(soup.get_text("|").split('|')) if r.status_code == 200 else ['Нет страницы']
            else:
                self.connection_err.append([link, f'{r.status_code}'])
                self.connection_errors()

            return models, links

    #
    def get_cars(self):
        dat = pd.DataFrame([])
        unpacker = lambda x, y: self.get_models(x)[y]
        lenght = len(self.urls['host'])
        dat['brand'] = self.brands.T[0]
        dat['model'], dat['modellink'] = dat.brand.apply(func=unpacker, y=0), dat.brand.apply(func=unpacker, y=1)
        dat = dat.apply(lambda x: x.explode()).reset_index(drop=True)
        dat['key'] = dat.modellink.apply(lambda x: x[lenght:] + 'used')
        dat = dat.drop(index=dat[dat.modellink.str.contains('spec.drom')].index)
        self.all_cars = dat.reset_index()
        dat.to_csv('all_cars_models.csv')
        return dat

    def region_exist(self, city):

        if isinstance(city, int) or str(city).isdigit():
            city = int(city)
            return city in self.regions.index
        elif city.isalpha():
            return city in self.regions.values
        else:
            raise Exception('Нет такого названия или номера региона в базе')
            # raise Exception('Нет такого названия региона в базе')

    def get_full_link(self, brand=None, model=None, city=None, string=None):
        if string != None:
            brand, model, city = string
        # Отработка истинности региона
        if self.region_exist(city):
            if isinstance(city, int) or str(city).isnumeric():
                link = self.regions.loc[int(city), 'link']
            elif city.isalpha():
                link = self.regions.query(f"region.str.contains('{city}')").link.values[0]
        else:
            link = self.urls['host']

        # Отработка истинности автомобилей
        if brand in self.all_cars.brand.values:
            if model in self.all_cars.model.values:
                dat = self.all_cars.query('brand == @brand and model == @model')
                # Создание ссылки
                model_link = dat.key.values[0]
                return link + model_link
            else:
                raise Exception('Нет такой модели машины в базе')
        else:
            raise Exception('Нет такой марки машины в базе')

    def page_reader(self, link):
        href_get = lambda x: x.get('href')
        with self.sess.get(link) as r:
            print(f'ответ страницы: {r.status_code}')
            if r.status_code == 200:
                html = r.text
                # css-10ib5jr e93r9u20
                # .find_all('a')
                soup = BeautifulSoup(html, 'html.parser') \
                    .find('div', class_='css-10ib5jr e93r9u20').find_all('a', class_='css-1psewqh ewrty961') \
                    if html != None else None
                res = list(map(href_get, soup)) if soup != [] or None else None
                return res
            else:
                self.connection_err.append([link, f'{r.status_code}'])
                self.connection_errors()

    def get_data_links(self, brand=None, model=None, city=None, page=100, string=None):
        if string != None:
            brand, model, city = string
        if self.region_exist(city):
            link_arr = np.array([], dtype=object)
            link = self.get_full_link(brand, model, city)
            pages = np.arange(1, page + 1, 1)
            print('Процесс сборки всех объявлений...')
            for i in pages:
                print(f'Сбор данных, машина: {brand}, {model}, регион: {city}\n страница № {i}')
                data = self.page_reader(link + f'/page{i}/')
                if isinstance(data, list):
                    link_arr = np.append(link_arr, data)
                else:
                    break
            return link_arr

    #
    def unpacker(self, link):
        d = {}
        # Получить описание авто
        with self.sess.get(link) as r:
            if r.status_code == 200:
                html = r.text
                soup = BeautifulSoup(html, 'html.parser') \
                    .find('div', class_='css-0 epjhnwz1')
                try:
                    # Получение цены
                    price = ''.join(soup.find('div', class_='css-1003rx0 e162wx9x0') \
                                    .get_text() \
                                    .split()[:-1])

                    price = int(price) if price.isnumeric() else np.nan
                    # Получение года
                    year_str = BeautifulSoup(html, 'html.parser') \
                        .find('h1', class_='css-1rmdgdb e18vbajn0') \
                        .getText('|').split()

                    year = year_str[year_str.index('год') - 1]
                    year = int(year) if year.isnumeric() else np.nan

                    date, views = BeautifulSoup(html, 'html.parser').find('div',
                                                                          class_="css-189eyu e1lm3vns0").get_text().split(
                        ' ')[-2:]
                    views = int(views) if views.isnumeric() else np.nan
                    # Получение описания
                    description = soup.find('tbody')
                    columns = description.find_all('th')
                    data = description \
                        .get_text('|').replace('л.с.', '').split('|')

                    table = np.array(columns)
                    data_arr = np.array(data)
                    d = {col[0]: data_arr[int(np.where(data_arr == col)[0] + 1)] for col in table}
                    d['year'] = year
                    d['price'] = price
                    d['views'] = views
                    d['date'] = date
                    d['link'] = link
                    self.linkcount += 1
                    print(f'Собрано объявление: {self.linkcount} / {self.linkvolume} ответ страницы: {r.status_code}')
                    return d
                except UnicodeDecodeError:
                    self.errors.append([link, 'Unicode_error'])
                    print(f'Проблема в {link}')
                    self.errlog('Unicide')
                except AttributeError:
                    self.errors.append([link, 'NoneType'])
                    print(f'Проблема в {link}')
                    self.errlog('Attribute')
            else:
                self.connection_err.append([link, f'{r.status_code}'])
                self.connection_errors()

    def get_car_data(self, links=None):
        links = np.array([links], dtype=object) if isinstance(links, str) else links
        links = links if isinstance(links, np.ndarray) else links
        if links is not None:
            self.linkvolume = links.size
            print('Процесс сборки данных с объявлений...')
            dat = pd.DataFrame(list(map(lambda x: self.unpacker(x), links)))
            self.linkcount = 0
            return dat.reset_index(drop=True)

    def errlog(self, city):
        with open(f'err_drom_{city}.txt', 'w') as f:
            f.write(str(self.errors))

    def connection_errors(self):
        with open(f'connection_errors.txt', 'w') as f:
            f.write(str(self.connection_err))

    def timers(self):
        with open(f'timing.txt', 'w') as f:
            f.write(str(self.timelists))

    def get_data(self, brand='all', model='all', city=77, page=100):
        dat = self.all_cars
        if self.region_exist(city):
            city = int(city) if isinstance(city, int) or str(city).isnumeric() else \
            self.regions.query(f'region.str.contains("{city}")').index[0]
        if brand == 'all':
            brandlist = dat.brand.values
        elif isinstance(brand, str):
            brandlist = np.array([brand])
        else:
            brandlist = np.array(tuple(brand))
        if model == 'all':
            modellist = dat.model.values
        elif isinstance(model, str):
            modellist = np.array([model])
        else:
            modellist = np.array(tuple(model))

        # Подгтовка DataFrame
        cardat = dat.copy()
        cardat = cardat.query('brand in @brandlist and model in @modellist')
        cardat['reg_id'] = city
        cardat['reg'] = self.regions.loc[city, 'region']
        cardat['link'] = np.nan
        cardat.link = cardat.link.astype('object')
        arr = cardat[['brand', 'model', 'reg_id']].values
        for i, row in enumerate(arr):
            brand, model, reg = row
            print(f'Сбор данных {i + 1} / {arr.shape[0]}, машина: {brand}, {model}, регион: {reg}')
            idx = cardat.query('(brand == @brand) & (model == @model) & (reg_id == @reg)').index[0]
            try:
                linklist = self.get_data_links(brand=brand, model=model, city=reg, page=page)
                cardat.at[idx, 'link'] = linklist if linklist.size != 0 else np.nan
            except UnicodeDecodeError:
                self.errors.append([row, 'Unicode_error'])
                print(f'Проблема в {row}')
                self.errlog(city)
            except AttributeError:
                self.errors.append([row, 'NoneType'])
                print(f'Проблема в {row}')
                self.errlog(city)
        print('Удаление строк без ссылок...')
        cardat = cardat.dropna(subset=['link'])
        print('Распределение по строкам...')
        cardat = cardat.explode(column='link')

        # сохранение кэша
        print(f'Кэширование региона с кодом {city}')
        cardat.to_csv(f'parsers/drom_ru_region_{city}_cash.csv', index=False)
        return cardat.reset_index(drop=True)

    def merger(self, cardat):
        city = cardat.reg_id.values[0]
        links = cardat.link.values
        linkdata = self.get_car_data(links)
        cardat = cardat.merge(linkdata, on='link')
        filename = f'parsers\cars_drom_region_{city}.csv'
        cardat.to_csv(filename, index=False)
        return cardat

    def collecter(self, code):
        self.linkcount = 0
        self.errors = []
        if not osp.exists(f'parsers/cars_drom_region_{code}.csv'):
            if not osp.exists(f'parsers/drom_ru_region_{code}_cash.csv'):
                start = time()
                dat = self.get_data(brand='all', model='all', city=code, page=100)
                end = time() - start
                self.timelists.append([f'Регион: {code}, Процесс: Сбор ссылок, Время: {end} c'])
            else:
                dat = pd.read_csv(f'parsers/drom_ru_region_{code}_cash.csv')
            start = time()
            dat = self.merger(dat)
            end = time() - start
            self.timelists.append([f'Регион: {code}, Процесс: Распаковка, Время: {end} c'])
            self.timers()
            return dat
        else:
            print(f'Файл с номером региона {code} уже существует')


t1 = time()
drom = drom()
codes = drom.regions.index
for code in codes:
    drom.collecter(code)
print(f'Общее время: {time() - t1}')