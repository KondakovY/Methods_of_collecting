"""1. Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию,
записывающую собранные вакансии в созданную БД."""

import requests
import re
import pandas as pd
from fake_headers import Headers
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from Lesson_3.Lesson_3_3 import insert_if_not_exists



URL_HH = 'https://hh.ru/search/vacancy'
URL_SJ = 'https://www.superjob.ru/vacancy/search/'
df_cols = ['Title', 'Salary (min)', 'Salary (max)', 'Currency', 'Link', 'Source']
vacancy = input('Введите название вакансии: ')      # название вакансии
pages = int(input('Введите кол-во страниц: '))
MONGO_HOST = 'mongodb://localhost:27017/'
DB_NAME = 'Lesson3'
COLLECTION_NAME = 'Vacancies'


def parse_salary(salaries):
    # зарплата мин/макс.
    min_salaries, max_salaries = [], []
    for sal in salaries:
        regex = re.findall(r'(\d+)', sal)
        if len(regex) > 1:
            min_salaries.append(regex[0])
            max_salaries.append(regex[1])
        elif len(regex) > 0:
            if sal.find(u'от') != -1:
                min_salaries.append(regex[0])
                max_salaries.append('')
            else:
                min_salaries.append('')
                max_salaries.append(regex[0])
        else:
            min_salaries.append('')
            max_salaries.append('')
    return min_salaries, max_salaries


def parse_hh_page(pg_num: int, **kwargs):
    home_url = 'https://hh.ru'
    hdr = kwargs.get('header', Headers(headers=True).generate())
    vcn = kwargs.get('vacancy', '')
    vacancy_param = {'text': vcn, 'page': pg_num}

    response = requests.get(URL_HH, params=vacancy_param, headers=hdr)

    soup = bs(response.text, 'lxml')

    vacancy_headers = [elem for elem in soup.find_all(class_='vacancy-serp-item__row_header')]
    titles = [elem.find(class_='resume-search-item__name').text for elem in vacancy_headers]
    links = [url.get('href') for elem in vacancy_headers for url in elem('a')]
    salaries = [salary.text.replace('\u202f', '') if (salary := elem.find(class_='vacancy-serp-item__sidebar')) else ''
                for elem in vacancy_headers]
    currencies = [spl[-1] if (spl := cur.split()) else '' for cur in salaries]


    min_salaries, max_salaries = parse_salary(salaries)

    return pd.DataFrame([titles, min_salaries, max_salaries, currencies, links, [home_url] * len(titles)],
                        index=df_cols).T


def parse_sj_page(pg_num: int, **kwargs):
    home_url = 'https://www.superjob.ru'
    hdr = kwargs.get('header', Headers(headers=True).generate())
    vcn = kwargs.get('vacancy', '')
    vacancy_param = {'keywords': vcn, 'page': pg_num}


    response = requests.get(URL_SJ, params=vacancy_param, headers=hdr)

    soup = bs(response.text, 'lxml')
    titles = [elem.text for elem in soup.find_all(class_='_6AfZ9')]
    links = [f'{home_url}{elem.get("href")}' for elem in soup.find_all(class_='_6AfZ9')]
    salaries = [elem.text.replace('\xa0', '') for elem in soup.find_all(class_=['_1qw9T'])]
    currencies = [regex.group(1) if (regex := re.search(r'\d(\D+)/', cur)) else '' for cur in salaries]


    min_salaries, max_salaries = parse_salary(salaries)

    return pd.DataFrame([titles, min_salaries, max_salaries, currencies, links, [home_url] * len(titles)],
                        index=df_cols).T


header = Headers(headers=True).generate()
df = pd.DataFrame(columns=df_cols)
for pg in range(pages):
    df = df.append(parse_sj_page(pg, header=header, vacancy=vacancy), ignore_index=True)
    df = df.append(parse_hh_page(pg, header=header, vacancy=vacancy), ignore_index=True)

df.drop_duplicates(inplace=True, ignore_index=True)
df.index = df.index + 1
df.to_csv('Lesson3.csv')

client = MongoClient('mongodb://localhost:27017/')
# get database and collection
db = client[DB_NAME]
db_collection = db[COLLECTION_NAME]

query = [{'title': df['Title'][i],
          'min_salary': df['Salary (min)'][i],
          'max_salary': df['Salary (max)'][i],
          'currency': df['Currency'][i],
          'link': df['Link'][i],
          'source': df['Source'][i]} for i in df.index]

insert_if_not_exists(query, host=MONGO_HOST, database=DB_NAME, collection=COLLECTION_NAME)