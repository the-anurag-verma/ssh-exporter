FROM python:3.10-slim

WORKDIR /app
COPY ssh_exporter.py .

RUN pip install prometheus_client paramiko

CMD ["python", "ssh_exporter.py"]