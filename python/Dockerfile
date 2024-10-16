# Use an official Python runtime as a parent image
FROM python:3.9-slim 

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY burn_cpu.py /app

# Install Flask
RUN pip install Flask

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=burn_cpu.py

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
