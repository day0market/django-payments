FROM python:3.8

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_HOME=/home/app/web
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME
COPY ./requirements.txt $APP_HOME
RUN pip install -r requirements.txt
COPY . $APP_HOME
ARG APP_USER=app
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}
RUN chown -R ${APP_USER}:${APP_USER} $APP_HOME
USER ${APP_USER}