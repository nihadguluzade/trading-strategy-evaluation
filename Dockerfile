FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /workspace

# Install the uv package manager
RUN pip install uv

# Copy ONLY the dependency files first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Sync dependencies (This creates the .venv inside the container)
RUN uv sync --frozen

# Copy source code (Railway doesn't support volumes, needs actual files)
COPY . .

# Expose port for Railway
EXPOSE 8000

# Start the FastAPI application
CMD ["uv", "run", "uvicorn", "src.engine.main:app", "--host", "0.0.0.0", "--port", "8000"]