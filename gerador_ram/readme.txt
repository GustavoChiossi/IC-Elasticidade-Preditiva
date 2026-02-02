Para usar o Dockerfile:
docker build -t gerador-ram .

Para usar um padrao:
PADRAO=<nome-do-padrao>

Os padroes sao:
constant | ascending | descending | wave | pos_exp | neg_exp | partial_random e total_random.

O parametro '-v' é usado para persistir no host arquivos gerados dentro do container, evitando que sejam perdidos quando o container é finalizado.

Quanto maior o numero do parametro STEPS, maior a duracao da execucao.

MAX_MB é o limite de memoria que a carga pode chegar. O valor não pode ser maior que o definido em "--memory".

Exemplo da execucao de um container:
docker run --rm --memory=1g -e PADRAO=wave -e MAX_MB=900 -e STEPS=200 -v $(pwd):/app gerador-ram