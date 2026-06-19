FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium browser
RUN playwright install --with-deps

# Start FastAPI server
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
