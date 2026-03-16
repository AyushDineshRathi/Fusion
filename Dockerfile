FROM python:3.9-slim

ENV FUSION_HOME=/home/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR ${FUSION_HOME}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        gcc \
        libjpeg62-turbo-dev \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ${FUSION_HOME}/requirements.txt

RUN pip install --no-cache-dir "pip<24.1" "setuptools<70" wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . ${FUSION_HOME}

RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

CMD ["bash", "docker-entrypoint.sh"]
