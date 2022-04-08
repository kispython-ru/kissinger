.PHONY: run
run:
	cd src && export CONFIG_PATH=default_config.yml && python src/main.py

.PHONY: install
install:
	apt update &&
	apt install software-properties-common -y &&
	add-apt-repository ppa:deadsnakes/ppa -y &&
	apt install python3.10 -y &&
	apt install python3.10-dev -y &&
	apt install python3.10-venv -y &&
	pip3 install poetry &&
	poetry install &&
	poetry shell

.PHONY: iusearchbtw
iusearchbtw:
	pacman -Suy python3-pip &&
	pip3 install poetry &&
	poetry install &&
	poetry shell