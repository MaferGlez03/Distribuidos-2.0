# Usa Python 3.10 como base
FROM python:3.10-alpine

WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt /app/

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

COPY ./chord.py /app/chord_dht/
COPY ./storage.py /app/chord_dht/
COPY ./handle_data.py /app/chord_dht/
COPY ./flexible_queue.py /app/chord_dht/
COPY ./certificate.pem /app/chord_dht/
COPY ./private_key.pem /app/chord_dht/

CMD ["python", "-u", "chord_dht/chord.py"]