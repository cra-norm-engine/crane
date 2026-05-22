FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace/backend

# Install sbom-tools pre-built binary (Linux x86_64, v0.1.20)
RUN apt-get update && apt-get install -y --no-install-recommends curl tar && \
    curl -fsSL https://github.com/sbom-tool/sbom-tools/releases/download/v0.1.20/sbom-tools-linux-x86_64.tar.gz \
        -o /tmp/sbom-tools.tar.gz && \
    tar -xzf /tmp/sbom-tools.tar.gz -C /tmp && \
    find /tmp -maxdepth 2 -name 'sbom-tools' -type f -exec cp {} /usr/local/bin/sbom-tools \; && \
    chmod +x /usr/local/bin/sbom-tools && \
    rm -rf /tmp/sbom-tools* && \
    apt-get purge -y curl && apt-get autoremove -y && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /workspace/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /workspace/backend

COPY entrypoint.sh /workspace/backend/entrypoint.sh
RUN chmod +x /workspace/backend/entrypoint.sh

WORKDIR /workspace/backend
ENTRYPOINT ["/workspace/backend/entrypoint.sh"]