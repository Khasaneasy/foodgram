[![Main Kittygram workflow](https://github.com/Khasaneasy/kittygram_final/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/Khasaneasy/kittygram_final/actions/workflows/main.yml)

# Продуктовый помощник Foodgram - дипломный проект студента 77 когорты Яндекс.Практикум 
- После запуска проект будут доступен по адресу: [здесь](http://foodhas.zapto.org)


- Документация будет доступна по адресу: [здесь](http://foodhas.zapto.org/api/docs/)

## Описание проекта Foodgram

«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.
Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд согласно рецепта/ов.


## Как развернуть
1. Скачайте docker-compose.yml из репозитория https://github.com/Khasaneasy/foodgram/blob/main/docker-compose.production.yml
2. Создайте файл .env
```
touch .env
```
3. Создайте файл с переменными окружения
```
POSTGRES_DB=<БазаДанных>
POSTGRES_USER=<имя пользователя>
POSTGRES_PASSWORD=<пароль>
DB_NAME=<имя БазыДанных>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<ключ Django>
DEBUG=<DEBUG True/False>
ALLOWED_HOSTS=<разрешенные хосты>
```

4. Запустите Dockercompose
```
sudo docker compose -f docker-compose.yml pull
sudo docker compose -f docker-compose.yml down
sudo docker compose -f docker-compose.yml up -d
```
5. Сделайте миграции и соберите статику
```
sudo docker compose -f docker-compose.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/ 
```

## Автодеплой на Git Hub Action
Добавьте перменные в Secrets
```
DOCKER_PASSWORD - пароль от Docker Hub
DOCKER_USERNAME - имя пользователя Docker Hub
HOST - ip сервера
SSH_KEY - ключ ssh для доступа к удаленному серверу
SSH_PASSPHRASE - пароль ssh
TELEGRAM_TO - id пользователя TELEGRAM
TELEGRAM_TOKEN - TELEGRAM токен
USER - имя пользователя сервера
```

#### В сервисе доступны следующие взаимодействия:
- Эндпоинты юзеров
    - users/ GET & POST
    - users/{id}/ GET
    - users/me/ GET
    - users/me/avatar/ GET, DELETE
    - users/set_password/ POST
    - auth/token/login/ POST
    - auth/token/logout/ POST
- Эндпоинты тэгов
    - tags/ GET тэгов
    - tags/{id}/ GET тэга
- Эндпоинты ингредиентов
    - tags/ GET 
    - tags/{id}/ GET
- Эндпоинты рецептов
    - recipes/ GET, POST
    - recipes/{id}/ GET, PATCH, DELETE
    - recipes/{id}/get-link/ GET
- Эндпоинты списка покупок
    - recipes/download_shopping_cart/ GET
    - recipes/{id}/shopping_cart/ POST, DELETE
- Эндпоинты избранного
    - recipes/{id}/favorite/ POST, DELETE
- Эндпоинты подписок
    - users/subscriptions/ GET
    - users/{id}/subscribe/ POST, DELETE


Используемые библиотеки:

Django==4.2.13
djangorestframework>=3.15.1
sqlparse=0.4.4
pytz=2024.1
djangorestframework-simplejwt>=4.7.2
djoser=2.1.0
python-dotenv==1.0.1
Pillow==10.3.0
django-filter==24.2
drf-extra-fields==3.7.0
reportlab==4.2.0
drf_base64==2.0
fpdf==1.7.2
django-cors-headers==3.13.0
psycopg2-binary==2.9.3 
shortener==0.2.1
shortuuid==1.0.13
gunicorn==20.1.0

Версия Python:
Python 3.9.10

Автор:

>https://github.com/Khasaneasy