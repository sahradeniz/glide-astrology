FROM python:3.11

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y build-essential

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
