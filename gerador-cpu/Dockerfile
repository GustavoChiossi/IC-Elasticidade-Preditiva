FROM python:3.11-slim

RUN pip install --no-cache-dir psutil matplotlib
COPY gerador_cpu.py /app/gerador_cpu.py
WORKDIR /app

ENV PADRAO=wave
ENV MAX_CPU=90
ENV CPU_CORES=1
ENV DURACAO=300
ENV CICLO=60

CMD ["python", "gerador_cpu.py"]