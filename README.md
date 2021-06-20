# Bike Intelligence Centre [BIC] :bike:
![Project](https://github.com/eguiwow/BIC/blob/master/bic/datacentre/static/images/bic_ejemplo.png)

Bike Intelligence Centre repository by [Ander Eguiluz Castañeira](https://twitter.com/andereguiluz)

## How to use it

BIC is accessible via [bizkaiabikeintelligence.deustotech.eu/datacentre](http://bizkaiabikeintelligence.deustotech.eu/datacentre) but if you want to run your own BIC platform follow these instructions:

## Prerequisites

* Django >= 2.0
* UNIX-like OS
* Virtualenvwrapper

## Installation of the PostgreSQL/PostGIS database

We add the ubuntugis ppa and download Postgres & PostGIS from it
```bash
sudo add-apt-repository ppa:ubuntugis/ppa
sudo apt-get update
sudo apt-get install postgis

```

## Configuration of the PostgreSQL/PostGIS database

Create a database and give it a password

Enable your database with PostGIS by connecting to your database and typing:
```PostgreSQL
your_db=# CREATE EXTENSION postgis;
```
In your `settings.py` file set your database user and password

## BIC dependencies

Install required BIC dependencies with requirements.txt file
```bash
pip install -r requirements.txt
pip install psycopg2-binary==2.8.6
```

## Usage

Access your project's path and run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
Then run the web server process
```bash
python manage.py runserver
```
You can access BIC via your browser: http://localhost:8000/datacentre 
