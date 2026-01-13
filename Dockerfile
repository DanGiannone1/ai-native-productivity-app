# Prism MCP Server Dockerfile
# Uses uv for fast, reproducible dependency management

FROM python:3.12-slim

WORKDIR /app

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files and source code before sync
# (uv sync needs src directory to build the project package)
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port 8000 for HTTP Stream Transport
EXPOSE 8000

# Run the MCP server using uv
CMD ["uv", "run", "python", "-m", "productivity_mcp.mcp_server"]
