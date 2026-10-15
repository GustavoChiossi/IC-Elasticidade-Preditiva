CONTAINER_RAM := carga-ram
CONTAINER_CPU := carga-cpu

build:
	cd gerador-ram && docker build -t gerador-ram .
	cd gerador-cpu && docker build -t gerador-cpu .

teste:
	docker run -d --name $(CONTAINER_RAM) --rm --memory=1g -e PADRAO=wave -e MAX_MB=800 -e DURACAO=900 -e CICLO=250 gerador-ram
	docker run -d --name $(CONTAINER_CPU) --rm --cpu-period=100000 --cpu-quota=400000 -e CPU_CORES=4 -e PADRAO=wave -e MAX_CPU=80 -e DURACAO=900 -e CICLO=250 gerador-cpu
	@sleep 5
	CONTAINERS=$(CONTAINER_RAM):ram,$(CONTAINER_CPU):cpu DURACAO_CONTROLADOR=910 python3 controlador.py
	python3 modulos/metricas.py $(CONTAINER_RAM)
	python3 modulos/metricas.py $(CONTAINER_CPU)
	@sleep 2
	python3 modulos/graficos.py $(CONTAINER_RAM)
	python3 modulos/graficos.py $(CONTAINER_CPU)