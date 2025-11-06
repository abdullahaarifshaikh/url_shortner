# Use an official Python slim base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code (the 'app' directory)
COPY ./app ./app

# Copy the frontend code
COPY ./frontend ./frontend

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
# We use 0.0.0.0 to make it accessible outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]