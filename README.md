#Simple payment app with simple API written on Django

##Features
* Send payments between accounts
* Query all payments
* Query all accounts

##Installation/run with docker
Simply run `docker-compose up --build` to run application in development mode. Production mode is not supported

##Raw installation
We assume you already cloned this repo. 
* `cd payment_app`
* change credentials in `.env_sample` or update `payment_app/settings.py` to use another file by default
* `python manage.py migrate`
* `python manage.py runserver`

You're done with installation

##Docs
API backed with swagger documentation. To access you can use `/payment_app/swagger.json` or online version.
To use interactive online version please run your app (in docker or natively). Than docs will be available at:
* [http://127.0.0.1:8000/swagger/](http://127.0.0.1:8000/swagger/)
* [http://127.0.0.1:8000/redoc/](http://127.0.0.1:8000/redoc/)

##Tests
To run tests please use default django test suite. `python manage.py test`