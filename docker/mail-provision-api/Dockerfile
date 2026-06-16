FROM python:3.12-slim-bookworm

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

RUN useradd -u 5000 -g 5000 -M -s /usr/sbin/nologin vmail 2>/dev/null || true

EXPOSE 8092
USER root
CMD ["python", "app.py"]
