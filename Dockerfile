FROM python:3.11

WORKDIR /app

COPY requirements.txt .      # ilk requirements.txt dosyasını kopyala
RUN pip install --no-cache-dir -r requirements.txt

COPY . .                     # sonra geri kalan dosyaları

CMD ["python", "app.py"]
