FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl wget ca-certificates \
    libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 \
    libpangocairo-1.0-0 libpango-1.0-0 libcairo2 \
    libatspi2.0-0 libx11-xcb1 libxcb1 libxext6 \
    libxfixes3 libxrender1 libxi6 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# ❗ FORCE fresh playwright install (NO CACHE)
RUN rm -rf /root/.cache/ms-playwright
RUN playwright install chromium

EXPOSE 8080

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
