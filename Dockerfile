FROM python:3.11-slim

# Print output straight away (for the interactive menu) and skip .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Expense records are saved here; mount a volume so they survive the container
# Create folder if doesnt exist, to store json file
RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD ["python", "main.py"]
