FROM python:3.14-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Run bot (webhook mode via env var)
CMD ["python", "-m", "tele_bot_dich"]
