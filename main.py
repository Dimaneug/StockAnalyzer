from bs4 import BeautifulSoup, NavigableString
import requests
import pandas as pd
from io import StringIO
import numpy as np
import os
import time

def return_row_index(table, name:str):
    try:
        return table['Unnamed: 0'].to_list().index(name)
    except:
        return None

def fill_indexes(table, columns:list):
    indexes = []
    for i, column in enumerate(columns):
        temp = return_row_index(table, column)
        indexes.append(temp)
    return indexes

def length_without_nan(values:list):
    count = 0
    for value in values[1:]:
        if not pd.isna(value):
            count += 1
    return count

def linear_regression(values:list):
    n = length_without_nan(values)
    x = list(val for val in range(1,n+1))
    y = list(float(val.replace(' ', '').replace('%','')) for val in values[1:] if not pd.isna(val))
    xy = sum(x[i]*y[i] for i in range(n))
    sx = sum(x)
    sy = sum(y)
    try:
        m = (n*xy - sx*sy) / (n*sum(x_*x_ for x_ in x) - sx*sx)
    except:
        return 
    return m

def find_median(values: list):
    return sum(float(val.replace(' ', '').replace('%','')) for val in values[1:] if not pd.isna(val))/len(values)

def get_verdict(m: float, median: float):
    if m == None or median == None:
        return
    if median * 0.01 > abs(m) or m == 0:
        return 'Ровно'
    elif median * 0.1 > abs(m):
        return 'Рост +/-' if m > 0 else 'Снижение +/-'
    else:
        return 'Рост' if m > 0 else 'Снижение'


def print_data(table: pd.DataFrame, indexes:list, columns:list, number_of_years: int):
    temp = []
    for i, index in enumerate(indexes):
        if index == None:
            continue
        nums = []
        for i in range(1, len(table.iloc[[index],:].values[0])):
            if i > number_of_years + 1:
                break
            nums.append(-i)
        nums.reverse()
        nums = [0]+nums
        if i == 0:
            temp.append(table.iloc[[index], nums].values[0])
        elif 0 < i < 9: 
            temp.append(table.iloc[[index], nums].values[0])
        else:
            temp.append(table.iloc[[index], nums].values[0])
    
    net_debt = [] # чистый долг
    print('-'*157)
    for i, val in enumerate(temp):
        if val[0] in columns[1:9]:
            if val[-1] == val[-2] or val[-1] == val[-3]:
                val = val[:-1]
            print('{:21s}'.format(val[0]), end=':   ')
            for item in val[1:]:
                if not pd.isna(item):
                    print('{:8s}'.format(item), end=' | ')
            print(get_verdict(linear_regression(val), find_median(val)))
            print('-'*157)
        elif val[0] == columns[15]:
            net_debt = [val[-j] for j in range(1,4)]
        elif val[0] == columns[16]:
            try:
                l_a = 0.0
                assets = [val[-j] for j in range(1,4)]
                for j in range(3):
                    if not pd.isna(net_debt[j]) and not pd.isna(assets[j]):
                        l_a = float(net_debt[j].replace(' ',''))/float(assets[j].replace(' ',''))
                        break
                print(f"{'L/A':25}:   {float(l_a)*100 if not pd.isna(l_a) else '-' :.2f}%")
                print('-'*157)
            except Exception as e:
                continue
        else:
            actual_data = 0
            for j in range(1, len(val)-1):
                if not pd.isna(val[-j]):
                    actual_data = -j
                    break
            print(f'{val[0]:25}:   {val[actual_data]}')
            print('-'*157)
        
    

sectors = ['НЕФТЕГАЗ', 'БАНКИ', 'МЕТАЛЛУРГИЯ', 'Э Генерация', 'Ритейл', 'Телеком', 'Транспорт', 'Строители', 'Машиностроение', 'Третий эшелон', 'Непубличные', 'ЭЛЕКТРОСЕТИ', 'ЭНЕРГОСБЫТ', 'РИТЕЙЛ', 'ПОТРЕБ', 'ТЕЛЕКОМ', 'ИНТЕРНЕТ', 'HIGH TECH', 'МЕДИА', 'ТРАНСПОРТ', 'СТРОИТЕЛИ', 'МАШИНОСТРОЕНИЕ', 'ТРЕТИЙ ЭШЕЛОН', 'НЕПУБЛИЧНЫЕ', 'ДРУГОЕ', 'Financials', 'Utilities', 'Consumer Discretionary', 'Consumer Staples', 'Energy', 'Healthcare', 'Industrials', 'Technology', 'Telecom', 'Materials', 'Real Estate', 'Consumer Cyclical', 'Communication Services', 'Other', 'ETF']
columns = ['Капитализация, млрд руб','Выручка, млрд руб', 'Чистый операц доход, млрд руб', 'EBITDA, млрд руб', 'Долг, млрд руб', 'Наличность, млрд руб', 'Чистая рентаб, %', 'ROE, %', 'ROA, %', 'P/E', 'EV/EBITDA', 'EPS, руб', 'P/BV', 'P/B', 'P/S', 'Чистый долг, млрд руб', 'Активы, млрд руб', 'Дост. общ капитала, %', 'Див доход, ао, %']

def main_func():
    sectors_dict = fill_sectors_dict()
    for key, value in sectors_dict.items():
        print("\n----- Сектор: "+ key+' -----')
        main = requests.get("https://smart-lab.ru/q/shares_fundamental/?sector_id%5B%5D="+str(value), headers={'User-Agent': 'Custom'})
        soup = BeautifulSoup(main.text, 'lxml')
        try:
            table = soup.find('table', class_='simple-little-table').children
        except:
            print("Нет таблицы!")
            continue
        for j, child in enumerate(table):
            if j > 11:
                break
            if (child != None) and (child != '\n') and (j != 1):
                name = child.find('a').text
                chart_icon = child.find('a', class_='charticon2')
                company_html = requests.get("https://smart-lab.ru"+chart_icon["href"]+"MSFO/download", headers={'User-Agent': 'Custom'})
                company_csv = pd.read_csv(StringIO(company_html.content.decode('utf-8')), sep=';', on_bad_lines='skip')
                indexes = fill_indexes(company_csv, columns)
                print(name)
                print_data(company_csv, indexes, columns)
                print(end='\n\n')
        wait = input("Нажмите Enter для следующей отрасли...")

def fill_sectors_dict():         
    main = requests.get("https://smart-lab.ru/q/shares_fundamental/", headers={'User-Agent': 'Custom'})
    soup = BeautifulSoup(main.text, 'lxml')
    sectors = soup.find('select', {"id": "sector_id"})
    sectors_dict = {}
    for child in sectors.contents: 
        if isinstance(child, NavigableString):
            continue 
        sectors_dict[child.text] = child.get("value")
    return sectors_dict

def interface(sectors_dict: dict):
    while 1:
        os.system("clear")
        print("Выберите сектор:")
        sectors_list = []
        i = 1
        for sector in sectors_dict.keys():
            sectors_list.append(sector)
            print(f"{i}. {sector}")
            i += 1
 
        choice = input("Введите номер сектора(q для выхода): ")
        if choice == 'q':
            quit()
        try:
            choice = int(choice)
        except:
            print("Вы ввели не номер!")
            wait = input()
            continue
        
        if choice > i or choice < 1:
            print("Вы ввели неправильный номер!")
            wait = input()
            continue
        os.system("clear")
        print_sector(sectors_list[choice-1], sectors_dict[sectors_list[choice-1]])

def print_sector(sector, index):
    
    main = requests.get("https://smart-lab.ru/q/shares_fundamental/?sector_id%5B%5D="+str(index), headers={'User-Agent': 'Custom'})
    soup = BeautifulSoup(main.text, 'lxml')
    try:
        table = soup.find('table', class_='simple-little-table').children
    except:
        print("Нет таблицы!")
        return
    for j, child in enumerate(table):
        if (child != None) and (child != '\n') and (j != 1):
            name = child.find('a').text
            chart_icon = child.find('a', class_='charticon2')
            company_html = requests.get("https://smart-lab.ru"+chart_icon["href"]+"MSFO/download", headers={'User-Agent': 'Custom'})
            company_csv = pd.read_csv(StringIO(company_html.content.decode('utf-8')), sep=';', on_bad_lines='skip')
            indexes = fill_indexes(company_csv, columns)
            os.system("clear")
            print("\n----- Сектор: "+ sector+' -----')
            print(name)
            print_data(company_csv, indexes, columns, 5)
            print(end='\n\n')
            wait = input("Продолжить?(q для выхода)")
            if wait == 'q':
                break


sectors_dict = fill_sectors_dict()
interface(sectors_dict)