build:
	docker build -t gerador .

run-wave:
	docker run --rm --memory=1g -e PADRAO=wave -e MAX_MB=900 -e DURATION=300 -v "$$(pwd)":/app -w /app gerador

run-neg:
	docker run --rm --memory=1g -e PADRAO=neg_exp -e MAX_MB=900 -e DURATION=300 -v "$$(pwd)":/app -w /app gerador

run-pos:
	docker run --rm --memory=1g -e PADRAO=pos_exp -e MAX_MB=900 -e DURATION=300 -v "$$(pwd)":/app -w /app gerador

run-const:
	docker run --rm --memory=1g -e PADRAO=constant -e MAX_MB=900 -e DURATION=120 -v "$$(pwd)":/app -w /app gerador

debug:
	docker run -it --rm --memory=1g -v "$$(pwd)":/app -w /app gerador bash