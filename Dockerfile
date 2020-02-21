FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install --no-cache-dir boto3 PyYAML email-validator

COPY ./registry ./logging_config.yaml /app/
