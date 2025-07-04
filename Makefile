.ONESHELL:
.DEFAULT_GOAL = help
.EXPORT_ALL_VARIABLES:

PATH := venv/bin:$(PATH)

ENV = .env.example
include $(ENV)


help:
	@ # Print help commands
	echo "Welcome To 'waka-readme-stats' GitHub Actions!"
	echo "The Action Can Be Tested Locally With : 'make run'."
	echo "NB! For Local Testing Python Version 3.8+ Is Required."
	echo "The Action Image Can Be Built Locally With : 'make container'."
	echo "NB! For Local Container Building Docker Version 20+ Is Required."
	echo "The Action Directory And Image Can Be Cleaned With : 'make clean'."
.PHONY: help

venv:
	@ # Install Python virtual environment and dependencies
	python3 -m venv venv
	pip install --upgrade pip
	pip install -r requirements.txt


run-locally: venv
	@ # Run action locally
	mkdir ./assets/ 2>/dev/null || true
	python3 ./sources/main.py
.PHONY: run-locally

run-container:
	@ # Run action in container
	docker build -t waka-readme-stats -f Dockerfile .
	docker run --env-file $(ENV) -v ./assets/:/waka-readme-stats/assets/ waka-readme-stats
.PHONY: run-container


lint: venv
	@ # Run flake8 and black linters
	flake8 --max-line-length=160 --exclude venv,assets .
	black --line-length=160 --exclude='/venv/|/assets/' .
.PHONY: lint

clean:
	@ # Clean all build files, including: libraries, package manager configs, docker images and containers
	rm -rf venv
	rm -rf repo
	rm -rf assets
	rm -f package*.json
	docker rm -f waka-readme-stats 2>/dev/null || true
	docker rmi $(docker images | grep "waka-readme-stats") 2> /dev/null || true
.PHONY: clean