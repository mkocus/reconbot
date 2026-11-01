FROM python:3.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY reconbot ./reconbot
COPY run.py .

# Run as an unprivileged user. UID 1000 matches the usual host user, so a
# characters.yaml mounted from the host with mode 600 stays readable.
RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin reconbot
USER reconbot

CMD ["python", "./run.py"]
