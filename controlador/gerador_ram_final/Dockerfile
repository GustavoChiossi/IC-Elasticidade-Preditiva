FROM python:3.11-slim

RUN pip install psutil matplotlib
COPY gerador-timestamp.py /app/
WORKDIR /app

ENV PADRAO=wave
ENV MAX_MB=850
ENV DURATION=180      
ENV INTERVAL=1.0      

CMD ["python", "gerador-timestamp.py"]