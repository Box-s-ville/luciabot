FROM python:3.9-alpine3.12

WORKDIR /usr/src/app

RUN apk update && apk add --virtual build-dependencies build-base gcc && apk add tzdata

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apk del build-dependencies

COPY . .

CMD [ "hypercorn", "bot:app", "-b", "0.0.0.0:8765" ]
