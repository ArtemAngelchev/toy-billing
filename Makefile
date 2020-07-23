.DEFAULT_GOAL := run-local

.PHONY: dependency run-local test db-migrate db-upgrade clean

dependency:
	poetry lock
	poetry export -f requirements.txt > requirements.release
	poetry export -E test -f requirements.txt > requirements.local
	poetry export --dev -E test -f requirements.txt > requirements.dev

run-local:
	docker-compose run --rm \
		--service-ports app-local

run:
	docker-compose run --rm \
		--service-ports app

test:
	docker-compose run --rm \
		--entrypoint "pytest $(filter-out $@,$(MAKECMDGOALS))" app-local
	docker-compose down --remove-orphans

db-migrate:
	docker-compose run --rm \
		--entrypoint "flask db migrate $(filter-out $@,$(MAKECMDGOALS))" app-local

db-upgrade:
	docker-compose run --rm --entrypoint "flask db upgrade head" app-local

clean:
	docker-compose down --remove-orphans

%:
	@:
