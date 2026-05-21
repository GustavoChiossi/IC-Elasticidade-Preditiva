run-all:
	@for p in pos_exp neg_exp; do \
		echo ">> $$p"; \
		docker run --rm -e PADRAO=$$p -e OUTPUT_SUFFIX=_$$p -v $$(pwd):/app -w /app gerador-ram-timestamp; \
	done

debug:
	docker run -it --rm --memory=1g -v $(pwd):/app -w /app gerador-ram-timestamp bash