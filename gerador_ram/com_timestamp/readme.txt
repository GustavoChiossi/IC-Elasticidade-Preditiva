Para usar o Dockerfile:
docker build -t gerador-ram .

Para usar um padrao:
PADRAO=<nome-do-padrao>

Os padroes sao:
constant | ascending | descending | wave | pos_exp | neg_exp | partial_random | total_random | wave_hard

O parametro '-v $(pwd):/app' é usado para persistir no host arquivos gerados dentro do container, evitando que sejam perdidos quando o container é finalizado.

MAX_MB é o limite de memoria que a carga pode chegar. O valor não pode ser maior que o definido em "--memory".

Os parâmetros são:

PADRAO=<nome-do-padrao>
MAX_MB=<int(mb)>
DURATION=<segundos>      
INTERVAL=<float>   

Exemplo da execucao de um container:
docker run --rm --memory=1g -e PADRAO="wave_hard" -v $(pwd):/app -w /app gerador-ram-timestamp  