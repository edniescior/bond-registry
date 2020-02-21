app-container = bond-registry
db-container = dynamodb-local

init:
	$(MAKE) build
	$(MAKE) up

build:
	docker-compose rm -vsf
	docker-compose down -v --remove-orphans
	docker-compose build

up:
	docker-compose up -d ${db-container}
	$(MAKE) migrate
	docker-compose up -d ${app-container}

migrate:
	cd ./localdb && \
	./init.sh
