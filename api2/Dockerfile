FROM python:3.11-alpine
WORKDIR /sesar-api
COPY requirements.txt /sesar-api/
RUN \
    # Needed for local aws credentials
    apk add --no-cache aws-cli && \
    # Needed for psycopg2
    apk add --no-cache postgresql-libs && \
    # Needed to build psycopg2
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    python3 -m pip install -r requirements.txt --no-cache-dir && \
    # Clean up psycopg2 build deps
    apk --purge del .build-deps

COPY . /sesar-api/

COPY ./start.sh /sesar-api/
CMD "/sesar-api/start.sh"