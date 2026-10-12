FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the tests first; start the app only if they all pass.
CMD ["sh", "-c", "python test.py && python main.py"]