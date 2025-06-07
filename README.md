
создайте env на примере env.example:

POSTGRES_DB_HOST=postgre_container
POSTGRES_DB_PORT=5432
POSTGRES_DB_USER=myuser
POSTGRES_DB_PASS=mypassword
POSTGRES_DB_NAME=main_postgresql_database


DEBUG=True




docker network create stripe-network

docker compose -f docker-compose-services.yml up -d

docker build -t django-image-stripe-app -f Dockerfile .

docker run --rm --network stripe-network --env-file .env django-image-stripe-app python manage.py migrate

docker run --rm -it --network stripe-network --env-file .env django-image-stripe-app python manage.py createsuperuser

docker compose -f docker-compose.yml up -d

docker run --rm --network stripe-network --env-file .env django-image-stripe-app python manage.py test


http://localhost/




dankupr21@gmail.com
4242 4242 4242 4242
12/34
123
Daniil Kupryianchyk
42424


Readme
    запуск - локально
    запуск - remote
        описание админки креды

кидаем ссылку на github

