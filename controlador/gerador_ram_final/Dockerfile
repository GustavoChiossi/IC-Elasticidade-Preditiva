FROM python:3.11-slim

RUN pip install psutil
COPY gerador.py /app/
WORKDIR /app

ENV PADRAO=wave
ENV MAX_MB=900
ENV DURACAO=300      
ENV INTERVALO=1.0      

CMD ["python", "gerador.py"]