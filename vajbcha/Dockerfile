FROM python:3.14-slim

RUN useradd -m vajbcha

EXPOSE 5000

ENV PORT=5000 \
  PYTHONUNBUFFERED=1 \
  DEBIAN_FRONTEND=noninteractive \
  PIP_ROOT_USER_ACTION=ignore

RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
  espeak-ng \
  && rm -rf /var/lib/apt/lists/*

RUN pip install "gunicorn==25.3.0"

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
RUN chown vajbcha:vajbcha /app

COPY --chown=vajbcha:vajbcha captcha captcha
COPY --chown=vajbcha:vajbcha app.py .

USER vajbcha

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
