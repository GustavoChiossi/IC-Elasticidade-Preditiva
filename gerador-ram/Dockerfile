FROM python:3.11-slim

RUN pip install --no-cache-dir psutil matplotlib
COPY gerador_ram.py /app/gerador_ram.py
WORKDIR /app

ENV PADRAO=wave
ENV MAX_MB=900
ENV DURACAO=300      
ENV CICLO=60

CMD ["python", "gerador_ram.py"]