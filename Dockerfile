# Use an official Python runtime as a parent image
FROM python:alpine

# Set the working directory in the container
WORKDIR /app

# Copy the application files into the container
COPY rssence.py /app/

# Install required Python dependencies
RUN pip install --no-cache-dir feedparser requests beautifulsoup4 feedgen toml openai

# Command to run the application
CMD ["python", "rssence.py"]
