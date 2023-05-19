# Social network Graphomaniac by [Denyacore](https://github.com/Denyacore)

Социальная сеть блогеров. Реализована идея вести свой блог с возможностью публикации постов, подпиской на группы и авторов, а также комментированием постов.


## Tech Stack

- [Python 3.7+](https://www.python.org/downloads/)
- [Django 2.2.16](https://www.djangoproject.com/download/)
- [Faker 12.0.1](https://pypi.org/project/Faker/)
- [mixer 7.1.2](https://pypi.org/project/mixer/)
- [Pillow 9.2.0](https://pypi.org/project/Pillow/)
- [pytest-django 4.4.0](https://pypi.org/project/pytest-django/)
- [pytest-pythonpath 0.7.3](https://pypi.org/project/pytest-pythonpath/)
- [pytest 6.2.4](https://pypi.org/project/pytest/)
- [requests 2.26.0](https://pypi.org/project/requests/)
- [six 1.16.0](https://pypi.org/project/six/)
- [sorl-thumbnail 12.7.0](https://pypi.org/project/sorl-thumbnail/)


## Authors

- [Denyacore](https://github.com/Denyacore)


## Deployment

To deploy this project run

1. Clone the repository and go to it on the command line:

```
https://github.com/Denyacore/hw05_final
```

```
cd hw05_final
```

2. Create and activate a virtual environment:

```
python3 -m venv env
        or
py -m venv venv
```

```
source venv/Scripts/activate
```
3. Upgrade installer
```
python3 -m pip install --upgrade pip
                or
py -m pip install --upgrade pip
```

4. Install dependencies from a file *requirements.txt* :

```
pip install -r requirements.txt
```

5. Make migrations in manage.py folder:

```
python3 manage.py migrate
            or
py manage.py migrate
```

6. Create superuser:

```
python manage.py createsuperuser
```

7. Launch a project in manage.py folder:

```
python3 manage.py runserver
            or
py manage.py runserver
```

 Project available at http://127.0.0.1:8000/ in your browser
