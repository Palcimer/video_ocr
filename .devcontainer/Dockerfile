FROM python:3.10-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git \
      curl \
      ca-certificates \
      build-essential \
      tesseract-ocr \
      tesseract-ocr-kor \
      libtesseract-dev \
      libleptonica-dev \
      libgl1 \
      libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip