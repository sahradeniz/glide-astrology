FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY ./swisseph-master ./swisseph-master

CMD ["python", "app.py"]
