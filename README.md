# Игорь зная что сюда заглянешь, что мне делать с этим фильтром :D????(RecipeFilter)

Находясь в папке infra, выполните команду docker-compose up. При выполнении этой команды контейнер frontend, описанный в docker-compose.yml, подготовит файлы, необходимые для работы фронтенд-приложения, а затем прекратит свою работу.

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.

# Продуктовый помощник Foodgram - дипломный проект студента 77 когорты Яндекс.Практикум 

После запуска проекта, он будет доступен по адресу http://127.0.0.1(локально)

## Описание проекта Foodgram

«Продуктовый помощник»: приложение, на котором пользователи публикуют рецепты кулинарных изделий, подписываться на публикации других авторов и добавлять рецепты в свое избранное.
Сервис «Список покупок» позволит пользователю создавать список продуктов, которые нужно купить для приготовления выбранных блюд согласно рецепта/ов.


### Запуск проекта локально

Для формирования базы из миграций, финальной настройки и заполнении базы тегами и ингридиентами,
а так же подтянуть статику, и создаем суперюзера:

```bash
python manage.py makemigrations
```

```bash
backend python manage.py migrate
```

```bash
python manage.py createsuperuser
```

Дополнительно можно наполнить DB ингредиентами и тэгами:

```bash
python manage.py add_tags
```

```bash
backend python manage.py add_ingrs
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


Версия Python:
Python 3.9.10

Автор:

>https://github.com/Khasaneasy