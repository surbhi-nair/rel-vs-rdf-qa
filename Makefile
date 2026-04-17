SHELL := /bin/bash

.PHONY: help build-docker build-docker-gpu run-docker run-docker-gpu test train clean

help:
	@echo "Available targets:"
	@sed -n '1,200p' Makefile | sed -n 's/^# //p' | sed '/^$$/q'

# build-docker: Build the CPU docker image.
# reads: requirements.txt, Dockerfile.cpu, src/
# produces: docker image surbhi-nair-project:cpu
# approx time: minutes (depends on network)
# approx RAM/disk: a few GB
build-docker:
	docker build -f Dockerfile.cpu -t surbhi-nair-project:cpu .

# run-docker: Run CPU image with mounted data and output.
# reads: /nfs/students/surbhi-nair
# produces: outputs in /extern/output
run-docker:
	docker run -it \
	  -v /local/data-hdd/nairs:/extern/data \
	  -v /nfs/students/surbhi-nair:/extern/archive \
	  --name surbhi-nair-project-cpu \
	  surbhi-nair-project:cpu

# FOR GPU, UNCOMMENT IF NEEDED
# 	docker build -f Dockerfile.gpu -t surbhi-nair-project:gpu .
#
# run-docker-gpu:
# 	docker run --gpus all -it \
# 	  -v /local/data-hdd/nairs:/extern/data \
# 	  -v /nfs/students/surbhi-nair:/extern/archive \
# 	  --name surbhi-nair-project-gpu \
# 	  surbhi-nair-project:gpu


test:
	pytest -q

train:
	python -m src.train --data /extern/data --out /extern/output

clean:
	rm -rf output/*

	# build-docker-gpu: