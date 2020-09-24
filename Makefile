app-container   = bond-registry
db-container    = dynamodb-local
fbeat-container = filebeat
es-container    = elasticsearch
kib-container   = kibana

init:
	$(MAKE) build
	$(MAKE) up
	$(MAKE) post

build:
	docker-compose rm -vsf
	docker-compose down -v --remove-orphans
	docker-compose build

up:
	docker-compose up -d ${es-container}
	docker-compose up -d ${kib-container}
	docker-compose up -d ${fbeat-container}
	docker-compose up -d ${db-container}
	$(MAKE) migrate
	docker-compose up -d ${app-container}

migrate:
	cd ./localdb && \
	./init.sh

post:
	cd ./kibana/config && \
	./setup.sh
