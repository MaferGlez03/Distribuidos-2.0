# Usar una imagen base oficial de Python
FROM python:3.9-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY . .

# Instala bash
RUN apk add --no-cache bash

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que Flask escucha
EXPOSE 5000

# Define el comando de entrada para el contenedor
ENTRYPOINT ["bash", "client.sh"]