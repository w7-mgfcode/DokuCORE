FROM python:3.10

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code monitor modules
COPY *.py ./

# Create default configuration directory
RUN mkdir -p /app/config

# Copy default configurations (if any)
COPY *.json /app/config/ 2>/dev/null || true

# Set environment variable defaults
ENV PYTHONUNBUFFERED=1
ENV WEBHOOK_ENABLED=false
ENV CHECK_INTERVAL=300

# Use the enhanced code monitor
CMD ["python", "enhanced_code_monitor.py"]