# Use the official Python image as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the contents of the spendvest_backend_py directory into the container at /app
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 80

# Check if site.db exists, if not, create it by executing models.py, then run the Flask application using Gunicorn
CMD ["sh", "-c", "if [ ! -f /app/site.db ]; then python3 /app/models.py; fi && gunicorn app:app"]
