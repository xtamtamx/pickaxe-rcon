FROM python:3.11-slim

WORKDIR /app

# Install SSH client
RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose web port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]