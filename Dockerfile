FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir numpy h5py

COPY Tesi_GEO_download.py /app/Tesi_GEO_download.py

# The launcher mounts the selected host directory here and sets it as WORKDIR.
WORKDIR /data

CMD ["python", "/app/Tesi_GEO_download.py"]
