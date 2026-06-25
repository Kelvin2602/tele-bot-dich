FROM python:3.12.2-slim

WORKDIR /app

# Install dependencies first (cached if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run bot
CMD ["python", "-m", "tele_bot_dich"]