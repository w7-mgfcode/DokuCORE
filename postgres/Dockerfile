FROM postgres:16

# Build dependencies installation
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16

# Clone and build pgvector
RUN git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && \
    make install