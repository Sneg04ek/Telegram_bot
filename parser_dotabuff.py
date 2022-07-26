import requests
import pandas as pd

from bs4 import BeautifulSoup
from fake_useragent import UserAgent


def heroes():
    '''
    Функция нужна для того, чтбы получить словарь из всех героев доты 2
    (ключ - имя героя) и ссылок на их дотабафы (значение - ссылка).
    '''
    url = 'https://www.dotabuff.com/heroes'
    headers = {'User-Agent': UserAgent().chrome}

    first_hero = 'Abaddon'  # Первый герой по списку
    last_hero = 'Zeus'  # Последний герой по списку

    response = requests.get(url,
                            headers=headers
                            )
    heroes = BeautifulSoup(response.text, 'html.parser')
    heroes = heroes.find_all('a')

    name_heroes = [hero.get_text().strip() for hero in heroes]
    url_heroes = [hero.get('href') for hero in heroes]

    index_first_hero = name_heroes.index(first_hero)
    index_last_hero = name_heroes.index(last_hero) + 1

    name_heroes = name_heroes[index_first_hero:index_last_hero]
    url_heroes = url_heroes[index_first_hero:index_last_hero]

    url_heroes = ['https://www.dotabuff.com' + url for url in url_heroes]

    results = dict(zip(name_heroes, url_heroes))

    return results


def get_info_about_hero(name_hero):
    '''
    Функция выдает информацию о герое по имени конкретного персонажа доты 2.
    Входные данные: имя персонажа в виде строки.
    Выходные данные: вся инфомрация по персонажу с сайта дотабаф.
    '''
    heroes_dict = heroes()
    url = heroes_dict[name_hero]

    headers = {'User-Agent': UserAgent().chrome}

    response = requests.get(url,
                            headers=headers
                            )
    hero = BeautifulSoup(response.text, 'html.parser')

    _, characteristic = hero.h1.get_text(separator='\n').split('\n')  # Тип атаки, роль, позиция

    popularity, win_rate = [char.get_text() for char in hero.find_all('dd')]  # Популярность, вин рейт

    hero_skills = dict()  # Способности героя и уровни прокачки

    # Здесь определяются названия способностей и талантов, которые должны прокачиваться на определенных уровнях
    for skill in hero.find_all(class_='line'):
        counter = 1  # Счетчик для определения уровня
        for level in skill:
            '''
            "icon" - иконка скилла или таланта,
            "empty" - на этом уровне скилл/талант не прокатичвается,
            "choice" - скилл/талант прокачивается
            '''
            guide = level['class']
            if 'icon' in guide:
                skill_name = level.img['alt']  # Достаем название скилла/таланта
                hero_skills[skill_name] = list()
            else:
                if 'choice' in guide:
                    hero_skills[skill_name].append(
                        str(counter))  # Добавляем уровни, на которых надо прокачивать конкретный скилл
                    counter += 1
                else:
                    counter += 1

    talents = dict()  # Лучшие таланты на каждом уровне

    # Достаем из таблицы по 2 таланта для каждого уровня, сравниваем их и выбираем лучший
    for group in hero.find_all(class_='talent-data-row'):
        talents_info = group.get_text(separator='\n').split('\n')  # Информация о двух талантах в виде списка

        level = int(talents_info[0])  # Уровень доступа к таланту

        talent_1_name = talents_info[3]  # Имя первого таланта из группы
        talent_2_name = talents_info[9]  # Имя второго таланта из группы

        talent_1_win_rate, talent_2_win_rate = [float(info.replace('Win Rate: ', '').replace('%', '')) \
                                                for info in talents_info if
                                                'Win Rate:' in info]  # Вин рейт с каждым из талантов

        if talent_1_win_rate > talent_2_win_rate:
            talents[level] = talent_1_name
        elif talent_2_win_rate > talent_1_win_rate:
            talents[level] = talent_2_name
        else:
            talents[level] = 'Без разницы'

    talents = dict(sorted(talents.items()))

    columns = ['name', 'win_rate',
               'matches']  # Наименования колонок для таблиц с лучшими и худшими противниками + предметами

    df_items = pd.DataFrame(columns=columns)  # Таблица с лучшими предметами для героя

    for item in hero.find_all('tbody')[2]:
        name_item, matches_with_item, _, win_rate_item = item.get_text(separator='\n').replace('%', '').split('\n')
        result = [name_item, win_rate_item, matches_with_item]
        df_items = df_items.append(dict(zip(columns, result)), ignore_index=True)

    df_items = df_items.sort_values(by='win_rate', ascending=False)

    df_best_versus = pd.DataFrame(columns=columns)  # Таблица с героями против которых мы лучше

    for opponent in hero.find_all('tbody')[3]:
        name_hero_best_versus, _, win_rate_best_versus, matches_best_versus = opponent.get_text(separator='\n').replace(
            '%', '').split('\n')
        result = [name_hero_best_versus, win_rate_best_versus, matches_best_versus]
        df_best_versus = df_best_versus.append(dict(zip(columns, result)), ignore_index=True)

    df_best_versus = df_best_versus.sort_values(by='win_rate', ascending=False)

    df_worst_versus = pd.DataFrame(columns=columns)  # Таблица с героями против которых мы хуже

    for opponent in hero.find_all('tbody')[4]:
        name_hero_worst_versus, _, win_rate_worst_versus, matches_worst_versus = opponent.get_text(
            separator='\n').replace('%', '').split('\n')
        result = [name_hero_worst_versus, win_rate_worst_versus, matches_worst_versus]
        df_worst_versus = df_worst_versus.append(dict(zip(columns, result)), ignore_index=True)

    df_worst_versus = df_worst_versus.sort_values(by='win_rate', ascending=True)

    return characteristic, \
           popularity, \
           win_rate, \
           hero_skills, \
           talents, \
           df_items, \
           df_best_versus, \
           df_worst_versus


def rewriting_info(characteristic, popularity, win_rate, hero_skills, talents, df_items, df_best_versus,
                   df_worst_versus):
    '''
    Функция преобразует различные данные собранные к единому формату.
    выходные данные: одна строка со всей информацией.
    '''
    characteristic = f'Тип атаки, роль в игре: {characteristic}\n'
    popularity = f'Позиция в топе самых популярных героев: {popularity}\n'
    win_rate = f'Процент побед: {win_rate}\n'

    hero_skills = ['Скиллы и уровни прокачки:\n'] + [f'{key}: {", ".join(value)}\n' for key, value in
                                                     hero_skills.items()]
    hero_skills = ''.join(hero_skills)

    talents = ['Лучшие таланты на своем уровне:\n'] + [f'Уровень {str(key)}: {value}\n' for key, value in
                                                       talents.items()]
    talents = ''.join(talents)

    skip = '              '  # Интервал между элементами для нормального отображения таблиц

    df_items = [f'Предмет{skip}% побед{skip}Матчи\n'] + [skip.join(row.values) + '\n' for idx, row in
                                                         df_items.iterrows()]
    df_items = ''.join(df_items)

    df_best_versus = [f'Герой{skip}% побед{skip}Матчи\n'] + [skip.join(row.values) + '\n' for idx, row in
                                                             df_best_versus.iterrows()]
    df_best_versus = ''.join(df_best_versus)

    df_worst_versus = [f'Герой{skip}% побед{skip}Матчи\n'] + [skip.join(row.values) + '\n' for idx, row in
                                                              df_worst_versus.iterrows()]
    df_worst_versus = ''.join(df_worst_versus)

    result = '\n'.join([
        characteristic,
        popularity,
        win_rate,
        hero_skills,
        talents,
        df_items,
        'Лучший против:\n',
        df_best_versus,
        'Худший против:\n',
        df_worst_versus
    ])

    return result
