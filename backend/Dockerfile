FROM python:3.12-slim

WORKDIR /app

# Copy only requirements first for caching
COPY req.txt .

# Install dependencies globally in the container
RUN pip install --no-cache-dir -r req.txt

# Copy backend code (excluding your local venv via .dockerignore)
COPY . .

EXPOSE 5000

CMD ["uvicorn", "acme.asgi:application", "--host", "0.0.0.0", "--port", "5000", "--reload"]
