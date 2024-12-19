include .build_info

pyi=pipenv run pyinstaller
version=v$(BUILD_VERSION)

build:
	$(pyi) setup.spec

pack:
	if not exist bin mkdir bin
	xcopy .\dist\cwi.exe .\bin\${BUILD_NAME}\\ /Y
	if not exist .versions mkdir .versions
	tar -cvf "./.versions/${BUILD_NAME}_${version}_${BUILD_PLATFORM}.zip" -C "./bin/" "${BUILD_NAME}"

clear-build:
	if exist build rd /s /q build
	if exist dist rd /s /q dist

clear-setup:
	if exist setuptools-build rd /s /q setuptools-build
	if exist "src/cwi.egg-info" rd /s /q "src/cwi.egg-info"

all: build pack clear-build

.PHONY:	build