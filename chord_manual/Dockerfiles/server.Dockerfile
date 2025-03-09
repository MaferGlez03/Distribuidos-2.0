# Usa python como base
FROM python:3.11-alpine

# Instala bash
RUN apk add --no-cache bash

# Establece el directorio de trabajo
WORKDIR  /app

# Copia toda la carpeta a app
COPY chord.py .
COPY handle_data.py .
COPY flexible_queue.py .
COPY storage.py .
COPY requirements.txt .
COPY server.sh .
COPY certificate.pem .
COPY private_key.pem .
RUN pip install -r requirements.txt

# Instala Python 3.10.12 y otras dependencias
#RUN pip install flask

# Expone el puerto 5000 para que otros contenedores accedan al servidor
EXPOSE 8000:8800

# Define el comando de entrada para el contenedor
ENTRYPOINT ["bash", "server.sh"]
