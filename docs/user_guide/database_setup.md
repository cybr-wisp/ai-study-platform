# One time local database setup

!!! Disclaimer
    This guide is written from memory so if it is missing any steps, please add them. Ask Cameron for help if needed.

## Prerequisites
1. PostgreSQL installed on your machine
2. Your venv is setup with all dependencies installed

## Setup
1. Connect to your Postgres server through the method of your choice (IntelliJ IDE database integration is recommended)
2. Run `CREATE TABLE "study-platform"`
3. In your repo's .env file, fill the details for DATABASE_* entries. DATABASE_URL should be `localhost`
4. With your venv active, cd into `services/api`
5. Run `python manage.py migrate`