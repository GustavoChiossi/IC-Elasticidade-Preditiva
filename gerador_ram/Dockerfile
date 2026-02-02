FROM python:3.11-slim

RUN pip install psutil matplotlib

WORKDIR /app
COPY gerador.py .

CMD ["python", "gerador.py"]
