FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN opentelemetry-bootstrap -a install

COPY . .

CMD ["opentelemetry-instrument", "--traces_exporter", "gcp_trace", "--metrics_exporter", "none", "--logs_exporter", "none", "python", "app.py"]
