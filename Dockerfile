FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /app

# Copy dependency manifest and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium browser binary
RUN playwright install chromium

# Copy application source code
COPY . .

# Expose standard Streamlit port
EXPOSE 8501

# Run Streamlit with cloud-proxy configurations enabled
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false"]