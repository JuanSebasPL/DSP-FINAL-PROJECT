# Base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy everything from your local api folder into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Command to run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]