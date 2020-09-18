FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install --no-cache-dir boto3 PyYAML email-validator python-json-logger # TODO: use a requirements file instead

COPY ./registry ./logging_config.yaml /app/
