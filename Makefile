include .env

pyi=pipenv run pyinstaller
version=v$(BUILD_VERSION)

build:
	$(pyi) setup.spec

pack:
	if not exist .versions mkdir .versions
	tar -cvf "./.versions/${BUILD_NAME}_${BUILD_PLATFORM}_${version}.zip" -C "./dist/" "${BUILD_NAME}.exe"
	if not exist bin mkdir bin
	move .\dist\${BUILD_NAME}.exe ./bin/
# I really hate windows style paths...

clear-build:
	if exist build rd /s /q build
	if exist dist rd /s /q dist

clear-setup:
	if exist setuptools-build rd /s /q setuptools-build
	if exist "src/cwi.egg-info" rd /s /q "src/cwi.egg-info"

all: build pack clear-build

.PHONY:	build