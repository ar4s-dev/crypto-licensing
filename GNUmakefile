#
# GNU 'make' file
# 

# PY[23] is the target Python interpreter.  It must have pytest installed.
PY2		?= python2
PY3		?= python3

VERSION=$(shell $(PY3) -c 'exec(open("crypto_licensing/version.py").read()); print( __version__ )')
TZ		?= Canada/Mountain

# To see all pytest output, uncomment --capture=no
PYTESTOPTS	= -vv  --capture=no --log-cli-level=DEBUG

PY3TEST		= TZ=$(TZ) $(PY3) -m pytest $(PYTESTOPTS)
PY2TEST		= TZ=$(TZ) $(PY2) -m pytest $(PYTESTOPTS)

.PHONY: all test clean upload
all:			help

help:
	@echo "GNUmakefile for cpppo.  Targets:"
	@echo "  help			This help"
	@echo "  test			Run unit tests under Python3"
	@echo "  install		Install in /usr/local for Python3"
	@echo "  clean			Remove build artifacts"
	@echo "  upload			Upload new version to pypi (package maintainer only)"


test2:
	$(PY2TEST)
test3:
	$(PY3TEST)

test:	test3 test2


doctest:
	$(PY3TEST) --doctest-modules


analyze:
	flake8 -j 1 --max-line-length=200 \
	  --ignore=W503,E201,E202,E221,E222,E223,E226,E231,E242,E251,E265,E272,E274 \
	  --exclude="crypto_licensing/ed25519.py" \
	  crypto_licensing

pylint:
	cd .. && pylint crypto_licensing --disable=W,C,R


build-check:
	@$(PY3) -m build --version \
	    || ( echo "\n*** Missing Python modules; run:\n\n        $(PY3) -m pip install --upgrade pip setuptools build\n" \
	        && false )

build:	build-check clean
	$(PY3) -m build
	@ls -last dist

dist/crypto_licensing-$(VERSION)-py3-none-any.whl: build

install:	dist/crypto_licensing-$(VERSION)-py3-none-any.whl
	$(PY3) -m pip install --force-reinstall $^


# Support uploading a new version of slip32 to pypi.  Must:
#   o advance __version__ number in slip32/version.py
#   o log in to your pypi account (ie. for package maintainer only)

upload: build
	python3 -m twine upload --repository pypi dist/*

clean:
	@rm -rf MANIFEST *.png build dist auto *.egg-info $(shell find . -name '*.pyc' -o -name '__pycache__' )


# Run only tests with a prefix containing the target string, eg test-blah
test-%:
	$(PY3TEST) *$*_test.py

unit2-%:
	$(PY2TEST) -k $*
unit3-%:
	$(PY3TEST) -k $*

unit-%:
	$(PY2TEST) -k $*
	$(PY3TEST) -k $*

#
# Target to allow the printing of 'make' variables, eg:
#
#     make print-CXXFLAGS
#
print-%:
	@echo $* = $($*)
	@echo $*\'s origin is $(origin $*)