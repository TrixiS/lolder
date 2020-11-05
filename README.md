# LOLDER
Client-server file storage service. (Toy YL project)

# Запуск
1. Установите [MongoDB](https://www.mongodb.com/try/download/community?tck=docs_server)
2. (Опционально) Создайте виртуальное окружение python3 -m "venv" venv и активируйте его
3. Установите зависимости pip install -r requirements.txt
4. Запустите сервер python3 start_server.py
5. Запустите клиент python3 start_client.py

# Конфигурация
1. Чтобы установить порт и хост сервера, измените значения os.environ (app_host и app_port)
2. Чтобы изменить порт, хост и название бд MongoDB для сервера, измените значения MONGODB_HOST, MONGODB_PORT, MONGODB_NAME в конфиге приложения Flask
3. Чтобы установить адрес сервера для клиента, измените значение os.environ server_address

**По дефолту севрер запустится на 127.0.0.1:8000, а данные для подключения к БД будут взяты эти - localhost, 27017, flask_app_db**
