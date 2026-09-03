FROM odoo:18.0

USER root

# Install development tools and dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    python3-dev \
    build-essential \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

USER odoo