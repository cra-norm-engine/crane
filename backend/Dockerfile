FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/backend

# Install sbom-tools and Trivy in a single layer to avoid /tmp permission issues
# across separate RUN steps. curl/tar are removed after both binaries are installed.
# Trivy (Aqua Security) — secondary SBOM vulnerability scanner; aggregates NVD,
# GHSA, OSV, Ubuntu, Debian, Alpine, RHEL for broader OS-level CVE coverage.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl tar \
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

COPY requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /workspace/backend

WORKDIR /workspace/backend
RUN chmod +x start.sh
CMD ["./start.sh"]
