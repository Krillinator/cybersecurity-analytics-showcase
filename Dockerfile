# Base image
FROM python:3.11-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files first (cache!)
COPY pyproject.toml uv.lock ./

# Install dependencies via uv
RUN uv sync --frozen

# Copy rest of app
COPY . .

# Expose port
EXPOSE 8000

# Run app via uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]