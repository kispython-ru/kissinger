#!/bin/sh
apt update
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
apt install python3.10 -y
apt install python3.10-dev -y
apt install python3.10-venv -y
apt install python3-pip -y
pip3 install poetry
poetry install
poetry shell