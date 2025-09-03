# Use the official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose the port your app runs on
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]