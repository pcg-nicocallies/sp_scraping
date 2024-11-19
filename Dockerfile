FROM python:3.12

RUN apt-get update && apt-get install -y \
    wget

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

RUN apt-get install -y ./google-chrome-stable_current_amd64.deb

ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

WORKDIR ${APP_HOME}

COPY ./src/ ./

RUN pip install -r requirements.txt

CMD ["python3", "verra.py"]