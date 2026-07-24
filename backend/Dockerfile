# syntax=docker/dockerfile:1
# ============================================================================
# Multi-stage build for the CRANE backend.
#
# Stage 1 (builder) installs all Python dependencies into an isolated
# virtualenv. Stage 2 (final) starts from a fresh slim image and copies only
# that venv, so pip, its build metadata and download cache never ship in the
# runtime image. Runtime-only assets (WeasyPrint's Pango/Cairo libraries, the
# sbom-tools and Trivy binaries, and Trivy's pre-warmed vulnerability DB) are
# installed directly in the final stage because they are needed at run time.
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — builder: resolve and install Python dependencies into /opt/venv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Build everything inside a self-contained virtualenv so the whole dependency
# tree can be copied to the final stage as a single directory.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# All third-party wheels are prebuilt (psycopg[binary], weasyprint, …), so no
# compilers / -dev headers are required here.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — final: slim runtime image with only what the app needs to run
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Put the copied virtualenv first on PATH so `python`/`uvicorn`/`alembic`
# resolve to the installed dependencies.
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /workspace/backend

# Install sbom-tools and Trivy in a single layer to avoid /tmp permission issues
# across separate RUN steps. curl/tar are removed after both binaries are installed.
# Trivy (Aqua Security) — secondary SBOM vulnerability scanner; aggregates NVD,
# GHSA, OSV, Ubuntu, Debian, Alpine, RHEL for broader OS-level CVE coverage.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl tar \
        # WeasyPrint runtime dependencies (PDF rendering via Pango/Cairo)
        libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-xlib-2.0-0 \
        shared-mime-info fonts-dejavu-core && \
    \
    # sbom-tools (SBOM quality analysis)
    curl -fsSL https://github.com/sbom-tool/sbom-tools/releases/download/v0.1.20/sbom-tools-linux-x86_64.tar.gz \
        -o /tmp/sbom-tools.tar.gz && \
    tar -xzf /tmp/sbom-tools.tar.gz -C /tmp && \
    find /tmp -maxdepth 2 -name 'sbom-tools' -type f -exec cp {} /usr/local/bin/sbom-tools \; && \
    chmod +x /usr/local/bin/sbom-tools && \
    rm -rf /tmp/sbom-tools* && \
    \
    # Trivy — use the official install script which picks the correct release URL
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
        | sh -s -- -b /usr/local/bin && \
    \
    apt-get purge -y curl && apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Pre-warm the Trivy vulnerability DB at image build time so first scan is fast.
RUN trivy image --download-db-only --no-progress || true

# Bring in the fully-installed Python environment from the builder stage.
COPY --from=builder /opt/venv /opt/venv

COPY . /workspace/backend

RUN chmod +x start.sh

# Document the port the server listens on. EXPOSE cannot read a runtime env var,
# so it is driven by a build ARG (default 8000). The actual listen port is set
# at run time by start.sh from ${BACKEND_PORT}; keep this ARG in sync via the
# compose build args for accurate image metadata.
ARG BACKEND_PORT=8000
EXPOSE ${BACKEND_PORT}

CMD ["./start.sh"]
