## 📌 Rishat Job Task
- Начало: 06.06.2025
- Завершение: 07.06.2025

### ⚙️ Технологии
- Django
- Stripe
- PostgreSQL
- Docker
- Nginx
- Unittest

### Remote Server Http (Not Secure)
http://185.250.44.183/
#### Django Admin Creads:
    - username: admin
    - password: admin


### Настройка в Docker

### Подготовка переменных окружения
Скопируйте файл .env.example в .env и заполните его следующим образом(пример):
```ini
POSTGRES_DB_HOST=postgre_container
POSTGRES_DB_PORT=5432
POSTGRES_DB_USER=myuser
POSTGRES_DB_PASS=mypassword
POSTGRES_DB_NAME=main_postgresql_database

STRIPE_SECRET_KEY_USD=
STRIPE_PUBLIC_KEY_USD=

STRIPE_SECRET_KEY_RUB=
STRIPE_PUBLIC_KEY_RUB=

DEBUG=True
```

### Создание docker-сети
```bash
docker network create stripe-network
```

### Запуск сервиса основной БД
```bash
docker compose -f docker-compose-services.yml up -d
```

### Сборка образа Django-приложения
```bash
docker build -t django-image-stripe-app -f Dockerfile .
```

### Применение миграций
```bash
docker run --rm --network stripe-network --env-file .env django-image-stripe-app python manage.py migrate
```

### Создание Супер пользователя для Django Admin
```bash
docker run --rm -it --network stripe-network --env-file .env django-image-stripe-app python manage.py createsuperuser
```

### Запуск оброзов Django + Nginx
```bash
docker compose -f docker-compose.yml up -d
```

### Приложение
http://localhost/


### Запуск тестов
```bash
docker run --rm --network stripe-network --env-file .env django-image-stripe-app python manage.py test
```
