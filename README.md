# Foodrgam

## Описание проекта
Cайт Foodgram(«Продуктовый помощник»). На этом сервисе пользователи могут публиковать рецепты, 
подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», 
а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или 
нескольких выбранных блюд.

## Используемые технологии:

Django 3.2

Python 3.7

Django REST Framework 3.14.0

PostgreSQL 

Nginx: 1.21.3-alpine

Gunicorn 20.0.4

Docker 20.10.22

Docker-compose v2.15.1

## Как запустить проект:

- Для развёртывания проекта на сервере необходимо скачать его локально на компьютер:
``` https://github.com/Eugene-Bykovsky/foodgram-project-react.git ```

- Добавьте на сервер файл docker-compose.yaml и nginx/default.conf, .env

- Рарверните проект на сервере с помощью github CI/CD


- Выполните миграции `docker-compose exec backend python manage.py migrate`
- Создайте суперюзера `docker-compose exec backend python manage.py createsuperuser`
- Соберите статику `docker-compose exec backend python manage.py collectstatic --no-input`
- Заполните базу готовым списком ингридиентов `docker-compose exec backend python manage.py load_data`.

## Развёрнутый проект
http://158.160.21.46/
http://158.160.21.46/admin/

## Пользователь
login: admin
password: the same

### Автор

Быковский Евгений
