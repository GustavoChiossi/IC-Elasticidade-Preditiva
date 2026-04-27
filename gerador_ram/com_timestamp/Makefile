run:
	docker run --rm --memory=1g -e PADRAO="wave_hard" -v $(pwd):/app -w /app gerador-ram-timestamp

run-all:
	@for p in constant ascending descending wave wave_hard pos_exp neg_exp partial_random total_random; do \
		echo ">> $$p"; \
		docker run --rm -e PADRAO=$$p -e OUTPUT_SUFFIX=_$$p -v $$(pwd):/app -w /app gerador-ram-timestamp; \
	done

debug:
	docker run -it --rm --memory=1g -v $(pwd):/app -w /app gerador-ram-timestamp bash