FROM python:3.11-slim

# Print output straight away (for the interactive menu) and skip .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached when only code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD ["sh", "-c", "python test.py && python main.py"]