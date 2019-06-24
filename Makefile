.SILENT:

## Colors
COLOR_RESET   = \033[0m
COLOR_INFO    = \033[32m
COLOR_COMMENT = \033[33m

PIP = sudo pip3
SUDO = sudo
PY_BIN = python3

## Help
help:
	printf "${COLOR_COMMENT}Usage:${COLOR_RESET}\n"
	printf " make [target]\n\n"
	printf "${COLOR_COMMENT}Available targets:${COLOR_RESET}\n"
	awk '/^[a-zA-Z\-\_0-9\.@]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf " ${COLOR_INFO}%-25s${COLOR_RESET} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

all: build build_arm install unit_test run

## Build docker image
build_image:
	sudo docker build . -f .infrastructure/Dockerfile -t wolnosciowiec/repairman

## Build
build_package:
	${PY_BIN} ./setup.py build

## Build documentation
build_docs:
	cd ./docs && make html

## Install
install: build_package
	${PIP} install -r ./requirements.txt
	${SUDO} ${PY_BIN} ./setup.py install
	which repairman
	make clean

## Clean up the local build directory
clean:
	${SUDO} rm -rf ./build ./repairman.egg-info

## Run unit tests
unit_test:
	${PY_BIN} -m unittest discover -s ./tests

## Generate code coverage
coverage:
	coverage run --rcfile=.coveragerc --source . -m unittest discover -s ./tests
