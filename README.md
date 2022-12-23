## Setup

- setup your python env

- run requirements.txt file to install python packages: ` pip3 install -r requirements.txt`

- setup postgreSql in you system

- make sure .env is populated  

- create database with same name as in env file

- run migration using `python3 manage.py migrate`

- start django server using : `python3 manage.py runserver` 

- run seeder in seeder folder

- Make a new user using dummy data
```{
  "username": "+911251423593",
  "password": "secret",
  "name": "Christiana",
  "phone": "+911251423593",
  "email": "Linda_Murazik@gmail.com"
}```


Use returned token to test other endpoints

