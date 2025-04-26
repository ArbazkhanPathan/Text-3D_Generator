FROM openfabric/tee-python-cpu:dev

# Install supervisord
RUN apt-get update && apt-get install -y \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies, including openfabric-pysdk and altair manually
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --upgrade poetry && \
    python3 -m pip install openfabric-pysdk==0.3.0 && \
    python3 -m pip install streamlit==1.12.0 requests==2.32.0 altair==4.2.2 && \
    python3 -m poetry config virtualenvs.create false && \
    python3 -m poetry install --only main --no-cache && \
    rm -rf ~/.cache/pypoetry/{cache,artifacts} ~/.cache/pip

# Copy the rest of the source code
COPY . .

# Ensure working directory is writable
RUN mkdir -p /app && chmod -R 777 /app

# Create supervisord configuration
RUN echo "[supervisord]\n\
nodaemon=true\n\
user=root\n\
\n\
[program:flask]\n\
command=python ignite.py\n\
autorestart=true\n\
stderr_logfile=/var/log/flask.err.log\n\
stdout_logfile=/var/log/flask.out.log\n\
\n\
[program:streamlit]\n\
command=streamlit run frontend.py --server.port=8501 --server.address=0.0.0.0\n\
autorestart=true\n\
stderr_logfile=/var/log/streamlit.err.log\n\
stdout_logfile=/var/log/streamlit.out.log" > /etc/supervisor/conf.d/supervisord.conf

# Expose ports for Flask (8888) and Streamlit (8501)
EXPOSE 8888 8501

# Start supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]