FROM python:3.9-slim

# Install ntpdate and git
RUN apt-get update && apt-get install -y ntpdate git && apt-get clean

# Set the working directory
WORKDIR /app

# Set the time zone
ENV TZ=Etc/UTC

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make start.sh executable
RUN chmod +x start.sh

# Command to sync system clock and start the bot
CMD ntpdate -s time.nist.gov && ./start.sh
