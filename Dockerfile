# Use official Python image from Docker Hub
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install NTP for time synchronization
RUN apt-get update && apt-get install -y ntp
RUN service ntp start

# Copy application code
COPY . .

# Command to run the bot
CMD service ntp start && python main.py
