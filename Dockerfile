FROM python:3.9-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. Installation de Chromium et Driver
# On retire les libs obsolètes (libgconf, libgl1-mesa) qui faisaient planter le build.
# 'chromium' va tirer automatiquement les bonnes dépendances modernes (libgtk, etc).
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libx11-xcb1 \
    wget \
    gnupg \
    unzip \
    fonts-liberation \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 2. Configuration dossier
WORKDIR /app

# 3. Installation dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copie du code
COPY . .

# 5. Variables d'environnement pour que ton script Python trouve les binaires
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 6. Lancement
CMD ["python", "linkedin_bot.py"]