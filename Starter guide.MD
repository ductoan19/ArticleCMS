## Create virtual environment
* py -m venv .venv
* .venv\Scripts\activate

## Install flask and depenencies
* pip install -r requirements.txt

## set env varibles
* $env:FLASK_APP= "application.py"
* $env:SQL_SERVER= "localhost:1433"
* $env:SQL_DATABASE= "ArticleCms"
* $env:SQL_USER_NAME= "local"
* $env:SQL_PASSWORD= "localpassword"

## Start the app
* flask run