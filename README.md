# Продуктовый помощник Foodgram - дипломный проект студента 77 когорты Яндекс.Практикум 

После запуска проекта, он будет доступен по адресу http://127.0.0.1(локально)

## Описание проекта Foodgram

«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.
Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд согласно рецепта/ов.


- Создать и запустить контейнеры Docker, выполнить команду на сервере
*(версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):*
```
sudo docker compose up
```

- После успешной сборки выполнить миграции:
```
sudo docker compose exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose exec backend python manage.py collectstatic --noinput
```

- Наполнить базу данных содержимым:
```
sudo docker compose exec backend python manage.py importcsv
```

- Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления

- После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)


- Документация будет доступна по адресу: [http://localhost/api/docs/](http://localhost/api/docs/)

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

flake8==6.0.0
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