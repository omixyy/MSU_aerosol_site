# MSU_aerosol_site

[![CI](https://github.com/omixyy/MSU_aerosol_site/actions/workflows/python-package.yml/badge.svg)](https://github.com/omixyy/MSU_aerosol_site/actions/workflows/python-package.yml)
[![code style: black & flake8](https://img.shields.io/badge/code%20style-black%20%7C%20flake8-blue.svg)](https://github.com/psf/black)
![Python Versions](https://img.shields.io/badge/Python-3.10%20%7C%203.11-yellow)

Сайт делался специально под нужды Географического Факультета МГУ имени М.В. Ломоносова. Он представляет собой систему, разработанную на Flask и bootstrap, реализующую систему работы с графиками, регистрацию и работу с базами данных для хранения приборов и комплексов.

## Инструкция к локальному запуску

1) Склонировать репозиторий или скачать zip архив

    ```bash
    git clone https://github.com/omixyy/MSU_aerosol_site
    ```

2) Создать виртуальное окружение

    ```bash
    python -m venv venv
    ```

3) Установить зависимости

    - Для продакшна

        ```bash
        pip install -r requirements/prod.txt
        ```

    - Для тестирования

        ```bash
        pip install -r requirements/test.txt
        ```

    - Для разработки

        ```bash
        pip install -r requirements/dev.txt
        ```

4) Перейти в основную папку проекта: msu_aerosol

    ```bash
    cd msu_aerosol
    ```

5) Создать первого админа

   ```bash
   flask createsuperuser
   ```

6) Запустить сайт

    ```bash
    python run.py
    ```

7) Зарегистрироваться как админ (войти в аккаунт, созданный в п. 5)
8) Зайти в админку
9) Добавить комплексы и приборы
10) Настроить приборы в домашней странице админки
11) Увидеть результат на главной странице

## Про переменные окружения

Принимается только одна - это YADISK_TOKEN. В неё необходимо положить Ваш токен для работы с Яндекс диском

## Админка

Администратор на админской странице может:

1) Изменять уже существующие записи
2) Создавать новые
3) Изменять статусы пользователей

## База данных

Ниже представлена ER-диаграмма базы данных
![alt text](ER.png)
