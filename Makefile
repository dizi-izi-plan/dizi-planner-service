.DEFAULT_GOAL := help

UV := uv run
MANAGE := $(UV) python src/manage.py

.PHONY: help install up down migrate makemigrations run test fmt lint check hooks shell build

help:  ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## Установить зависимости и pre-commit хук
	uv sync
	$(UV) pre-commit install

up:  ## Поднять postgres в docker
	docker compose up -d

down:  ## Остановить контейнеры
	docker compose down

migrate:  ## Применить миграции
	$(MANAGE) migrate

makemigrations:  ## Создать миграции
	$(MANAGE) makemigrations

run:  ## Запустить dev-сервер
	$(MANAGE) runserver

test:  ## Запустить тесты
	$(UV) pytest

fmt:  ## Отформатировать код
	$(UV) ruff format src

lint:  ## Прогнать линт
	$(UV) ruff check src

check:  ## Django system check
	$(MANAGE) check

hooks:  ## Прогнать pre-commit на всех файлах
	$(UV) pre-commit run --all-files

shell:  ## Django shell
	$(MANAGE) shell

build:  ## Собрать prod-образ
	docker build -t dizi-planner:latest .
