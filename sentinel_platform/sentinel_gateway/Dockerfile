# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

# Install build dependencies (gcc needed for some python libs)
RUN apt-get update && apt-get install -y gcc \
    && pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Update PATH to use installed pip packages
ENV PATH=/root/.local/bin:$PATH

# Optimization: Turn off python buffering for instant logs
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]