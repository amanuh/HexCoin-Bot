# Use a lightweight Python image
FROM python:3.9-slim

# Install ntpdate
RUN apt-get update && apt-get install -y ntpdate

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make start.sh executable
RUN chmod +x start.sh

# Sync system clock at container start and start the bot
CMD ntpdate -s time.nist.gov && ./start.sh
