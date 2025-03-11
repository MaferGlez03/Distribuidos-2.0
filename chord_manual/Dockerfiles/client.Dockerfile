# Usa Python como base
FROM python:3.11-slim

# Instala dependencias del sistema necesarias para tkinter y PIL
RUN apt-get update && apt-get install -y \
    python3-tk \
    libgl1-mesa-glx \
    libx11-6 \
    libxft2 \
    libxext6 \
    iproute2 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos al contenedor
COPY client.py .
COPY client.sh .
COPY requirementsC.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirementsC.txt
RUN pip install --no-cache-dir customtkinter Pillow

# Ejecuta un servidor gráfico virtual y el cliente
ENTRYPOINT ["bash", "-c", "Xvfb :99 -screen 0 1024x768x16 & export DISPLAY=:99 && bash client.sh"]
