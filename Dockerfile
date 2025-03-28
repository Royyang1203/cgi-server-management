FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ipmitool && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p instance

# Copy the rest of the application
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SQLALCHEMY_DATABASE_URI=sqlite:///instance/mydb.sqlite

# Create an initialization script
RUN echo '#!/bin/bash\n\
if [ ! -f /app/instance/mydb.sqlite ]; then\n\
    python init_servers.py\n\
fi\n\
flask run --host=0.0.0.0' > /app/start.sh && \
    chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["/app/start.sh"] 