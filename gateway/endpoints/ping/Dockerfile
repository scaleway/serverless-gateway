FROM python:3.10-alpine

RUN apk update
RUN pip3 install flask

WORKDIR /app
COPY server.py .

CMD python3 server.py
