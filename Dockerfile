FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements first (take advantage of Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the rest of the application files
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Default command to run the app
CMD ["python", "run.py"]