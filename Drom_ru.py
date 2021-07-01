from bs4 import BeautifulSoup
import requests as req
import numpy as np
import pandas as pd
import os.path as osp
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
            .find('div', class_='css-1xdu4vx ete74kl0') \
            .find_all('a')
        self.brands = np.unique(brands_soup).T

            # Города:
        cities_soup = BeautifulSoup(self.html_cities, 'html.parser') \
            .find('div', class_='b-selectCars b-media-cont') \
            .find_all('a')
        self.cities = (np.array(cities_soup).T)[0]

        # Кэш
            # Регионы
        try:
            dat = pd.read_csv('region_data.csv', index_col=0)
            self.regions = dat
        except IOError:
            self.regions = None
            print('File with region data not exist, use function: ".get_regions()"')

            # Каталог машин
        try:
            self.all_cars = pd.read_csv('all_cars_models.csv', index_col=0)
        except IOError:
            self.all_cars = None
            print('File with car data not exist, use function: ".get_cars()"')

        # self.brand = None
        # self.models = None
        # self.city = None

    def get_regions(self):
        # Получить кэш регионов
        html = self.html_cities
        dat = pd.DataFrame([], columns=[ 'id', 'region', 'link'])
        soup = BeautifulSoup(html, 'html.parser')\
            .find('div', class_='b-selectCars b-media-cont')
        text = soup.find_all('a', class_='b-link')
        links = soup\
            .find_all('a', class_='b-link', href=True)
        reg_arr =  np.array(text)
        link_arr = np.array([])
        for link in links:
            link_arr = np.append(link_arr, link['href'])

        dat['link'] = link_arr
        dat['region'] = reg_arr

        dat2 = dat.copy()
        dat2.loc[29, 'link'] = 'https://auto.drom.ru/region77/'
        dat2.loc[63, 'link'] = 'https://auto.drom.ru/region78/'

        reg =lambda x:  int(re.findall(r'[0-9]+', x)[0])
        dat2.id = dat2.link.apply(reg)
        dat2.sort_values(by='id', inplace=True)
        dat2.set_index('id', inplace=True)
        dat2.to_csv('region_data.csv')
        self.regions = dat2
        return dat2


    def get_city_link(self, city):
        # Получатель ссылки города
        soup = BeautifulSoup(self.html_cities, 'html.parser') \
            .find(class_='b-selectCars b-media-cont')\
            .find('a', text=city)\
            .get('href')
        return soup

    def get_brand_link(self, brand):
    # Получатель ссылки бренда
        if brand in self.brands:
            soup = BeautifulSoup(self.html_brands, 'html.parser') \
            .find('div', class_='css-1xdu4vx ete74kl0') \
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
                    .find('div', class_='css-1xdu4vx ete74kl0') \
                    .get_text("|").split('|')
                models = np.array(soup)
                return models

    def get_model_link(self, brand='ГАЗ', model='31105 Волга'):
        if (brand in self.all_cars.brand.values) and (model in self.all_cars.model.values):
            url = self.get_brand_link(brand)
            with req.get(url, headers=self.headers) as r:
                if r.status_code == 200:
                    html_models = r.text
                    link = BeautifulSoup(html_models, 'html.parser') \
                        .find(text=model)\
                        .findParent()\
                        .get('href')
                    return link

    def get_cars(self):

        dat = pd.DataFrame([], columns=['brand', 'model'])
        dat['brand'] = self.brands
        dat['model'] = dat.brand.apply(self.get_models)
        dat = dat.explode(column='model').reset_index(drop=True)
        self.all_cars = dat
        dat.to_csv('all_cars_models.csv')
        return dat

    def region_exist(self, city):
        if str(city).isdigit():
            city = int(city)
            if city in self.regions.index:
                return 'digit'
            else:
                raise Exception('Нет такого номера региона в базе')
        elif city.isalpha():
            val = self.regions.query(f'region.str.contains("{city}")').link.values
            if val.size != 0:
                return 'word'
            else:
                raise Exception('Нет такого названия региона в базе')

    def get_full_link(self, brand=None, model=None, city=None, string=None):
        if string != None:
            brand = string[0]
            model = string[1]
            city = string[2]
        # Отработка истинности региона
        if self.region_exist(city) == 'digit':
            link = self.regions.loc[int(city), 'link']
        elif self.region_exist(city) == 'word':
            link = self.regions.query(f"region.str.contains('{city}')").link.values[0]
        else:
            link = 'https://auto.drom.ru/'

        # Отработка истинности автомобилей
        if brand in self.all_cars.brand.values:
            if model in self.all_cars.model.values:
                # Создание ссылки
                model_link = self.get_model_link(brand=brand, model=model)[28:] + 'used/'
                return link + model_link
            else:
                raise Exception('Нет такой модели машины в базе')
        else:
            raise Exception('Нет такой марки машины в базе')

    def get_data_links(self, brand, model, city, page=100):
        link = self.get_full_link(brand, model, city)
        link_arr  = np.array([])
        for i in range(1, page):
            link2 = link + f'page{i}/'
            with req.get(link2, headers=self.headers) as r:
                if r.status_code == 200:
                    html = r.text
                    soup = BeautifulSoup(html, 'html.parser') \
                        .find('div', class_='css-10ib5jr e93r9u20') \
                        .find_all('a', class_="css-1psewqh ewrty961")
                    if soup != []:
                        for item in soup:
                            link_arr = np.append(link_arr, item['href'])
                    else:
                        break
        return link_arr

    def get_car_data(self, link):
        # Получить описание авто
        with req.get(link, headers=self.headers) as r:

            if r.status_code == 200:
                html = r.text
                soup = BeautifulSoup(html, 'html.parser')\
                        .find('div', class_='css-0 epjhnwz1')
                # Получение цены
                price = ''.join(soup.find('div', class_='css-1003rx0 e162wx9x0')\
                .get_text()\
                .split()[:-1])
                if price.isnumeric():
                    price = int(price)
                else:
                    price = np.nan
                # Получение цены
                year_str = BeautifulSoup(html, 'html.parser')\
                        .find('h1', class_='css-1rmdgdb e18vbajn0')\
                        .getText('|').split()

                year = year_str[year_str.index('год') - 1]
                if year.isnumeric():
                    year = int(year)
                else:
                    year = np.nan
                # Получение описания
                description = soup.find('tbody')
                columns = description.find_all('th')
                data = description\
                .get_text('|').replace('л.с.', '').split('|')
                d = {}
                table = np.array(columns)
                data_arr = np.array(data)
                for col in table:
                    idx = int(np.where(data_arr == col)[0])
                    d[col[0]] = data_arr[idx+1]
                dat = pd.DataFrame([d])
                dat['year'] = year
                dat['price'] = price
                dat['link'] = link
                return dat

    def errlog(self, file, city):
        with open(f'err_drom_{city}.txt', 'w') as f:
            f.write(str(file))

    def get_data(self, brand='all', model='all', city=77):

        global errlist
        dat = self.all_cars

        if self.region_exist(city) == 'word':
            city = self.regions.query(f'region.str.contains("{city}")').index[0]
        elif self.region_exist(city) == 'digit':
            city = int(city)
        else:
            raise Exception('Город не найден')
        if brand == 'all':
            brandlist = dat.brand.values
        elif isinstance(brand, str):
            brandlist = np.array([brand])
        else:
            brandlist = np.array(tuple(brand))

        # Подгтовка DataFrame

        cardat = dat.copy()
        cardat = cardat[cardat.brand.isin(brandlist)]
        cardat['reg_id'] = city
        cardat['reg'] = self.regions.loc[city, 'region']
        cardat['link'] = np.nan
        cardat.link = cardat.link.astype('object')
        arr = cardat[['brand', 'model', 'reg_id']].values
        print('Процесс сборки всех объявлений...')

        for i, row in enumerate(arr):
            print(f'Сбор данных {i+1} / {arr.shape[0]}, машина: {row[0]}, {row[1]}, регион: {row[2]}')
            idx = cardat.query(f'(brand == "{row[0]}") & (model == "{row[1]}") & (reg_id == {row[2]})').index[0]
            try:
                linklist = self.get_data_links(brand=row[0], model=row[1], city=row[2])
                if linklist.size != 0:
                    cardat.at[idx, 'link'] = linklist
            except UnicodeDecodeError:
                errlist.append([row, 'Unicode_error'])
                print(f'Проблема в {row}')
                self.errlog(errlist, city)
            except AttributeError:
                errlist.append([row, 'NoneType'])
                print(f'Проблема в {row}')
                self.errlog(errlist, city)
        print('Удаление строк без ссылок...')
        cardat = cardat.dropna(subset=['link'])
        print('Распределение по строкам...')
        cardat = cardat.explode(column='link')

        # сохранение кэша
        print(f'Кэширование региона с кодом {city}')
        cardat.to_csv(f'parsers\drom_ru_region_{city}_cash.csv', index = False)
        return cardat

    def unpack_links(self, cardat):
        global errlist
        city = cardat.reg_id.values[0]
        linkdata = pd.DataFrame([])
        links = cardat.link.values
        if links.size !=0:
            print('Процесс сборки данных с объявлений...')
            for i, link in enumerate(links):
                print(f'Сборка доступных объявлений {i+1} / {links.shape[0]}')
                try:
                    linkdata = linkdata.append(self.get_car_data(link))
                except UnicodeDecodeError:
                    errlist.append([link, 'Unicode_error'])
                    print(f'Проблема в {link}')
                    self.errlog(errlist, city)
                except AttributeError:
                    errlist.append([link, 'NoneType'])
                    print(f'Проблема в {link}')
                    self.errlog(errlist, city)
            cardat = cardat.merge(linkdata, on='link')
        else:
            errlist.append([f'No links in region: {city}'])
            self.errlog(errlist, city)

        filename = f'parsers\cars_drom_region_{city}.csv'
        cardat.to_csv(filename, index=False)
        return cardat

drom = drom()
regions = drom.regions.index.values
errlist = []
for i, code in enumerate(regions):
    print(code)
    print(f'регион {i + 1} / {regions.shape[0]}')
    if osp.exists(f'parsers/cars_drom_region_{code}.csv') == False:
        if osp.exists(f'parsers/drom_ru_region_{code}_cash.csv') == False:
            dat = drom.get_data(brand='all', city=code)
        else:
            dat = pd.read_csv(f'parsers/drom_ru_region_{code}_cash.csv')
        drom.unpack_links(dat)
    else:
        print(f'Файл с номером региона {code} уже существует')