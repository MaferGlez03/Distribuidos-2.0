# Usa python como base
FROM python:3.11-alpine

# Instala bash
RUN apk add --no-cache bash

# Establece el directorio de trabajo
WORKDIR  /app

# Copia toda la carpeta a app
COPY  client.py .
COPY client.sh .

# Instala Python 3.10.12 y otras dependencias
RUN pip install requests

# Define el comando de entrada para el contenedor
ENTRYPOINT ["bash", "client.sh"]
