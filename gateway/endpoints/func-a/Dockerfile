FROM python:3.10-alpine

RUN apk update
RUN pip3 install scaleway_functions_python

WORKDIR /app
COPY server.py .

CMD python3 server.py
