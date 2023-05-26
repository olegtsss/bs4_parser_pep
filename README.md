# Описание проекта parser_yap:

Учебный проект парсинга документации Python:
- главная страница c документацией Python (https://docs.python.org/3/)
- главная страница c информацией о PEP (https://peps.python.org/)
- страница для скачивания документации Python (https://docs.python.org/3/download.html)

### Используемые технологии:

Python 3.7, кеширование веб-страниц, DOM парсинг HTML

### Как запустить проект:
Клонировать репозиторий, перейти в него в командной строке:
```
git clone https://github.com/olegtsss/parser_yap.git
cd parser_yap
python -m venv venv
. venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```


### Доступные аргументы командной строки
Для просмотра режимов работы парсера в терминале введите команду ```-h```
или ```--help```:  
```
python src/main.py -h
```

Результат работы команды будет следующим:
```
"23.05.2023 22:28:49 - [INFO] - Парсер запущен!"
usage: main.py [-h] [-c] [-o {pretty,file}]
               {whats-new,latest-versions,download,pep}

Парсер документации Python

positional arguments:
  {whats-new,latest-versions,download,pep}
                        Режимы работы парсера

optional arguments:
  -h, --help            show this help message and exit
  -c, --clear-cache     Очистка кеша
  -o {pretty,file}, --output {pretty,file}
                        Дополнительные способы вывода данных
```

### Вывод информации осуществляется:  
- в консоль (stdout);  
- в консоль в табличном виде (```-o pretty```);
- в формате csv (```-o file```);

Настроено логирование работы парсера (```/src/logs/```).

### Примеры запуска:

```
Запуск парсера информации из статей о нововведениях в Python
python src/main.py whats-new

C очисткой кеша
python src/main.py whats-new -c

C сохраннием в файле
python src/main.py whats-new --output file

Запуск парсера статусов версий Python
python src/main.py latest-versions

Запуск парсера, который скачивает архив документации Python
python src/main.py download

Запуск парсера и получение статистики по PEP
python src/main.py pep
```
### Разработчик:
[Тимощук Олег](https://github.com/olegtsss)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=whte)
