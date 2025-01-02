# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11

LABEL name="conery/op-client"
LABEL maintainer="conery@uoregon.edu"

WORKDIR /app

COPY requirements.txt /app
RUN python -m pip install -r requirements.txt

COPY ./src /app/src
COPY ./site /app/site

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 5006

ENV OP_PROJECT=demo

CMD python src/main.py --server ${OP_SERVER} --project ${OP_PROJECT}

