# Yatube

Yatube - Социальная сеть для публикации личных дневников.

Поддерживается следующий функционал:

- Публикация записей с изображениями.
- Публикация записей в сообщества.
- Комментарии к записям других авторов.
- Подписка на других авторов.
- Лента с записями, на которых оформлена подписка.
- Для проекта написаны тесты Unittest.

## Установка

Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/klassnenkiy/hw05_final.git
```
```
cd hw05_final
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```

Выполнить миграции:
```
python3 manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver
```
