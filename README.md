# car-pooling
проект для учебной практики в ИТМО

Инструкция по запуску проекта:
- склонировать репозиторий
- активировать виртуальную среду venv
- из корня проекта запустить `pip install -r requirements.txt`
- `cd .\carpool_project\`
- `python manage.py migrate`
- `python manage.py seed_data`
- `python manage.py collectstatic`
- `daphne -b 127.0.0.1 -p 8000 carpool.asgi:application`
