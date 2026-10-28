# Zoning Capacity Explorer: one command per pipeline step.
#   make all CITY=pasadena     download + clean
#   make test                  unit tests
#   make exercise              tests for the current learning exercise

CITY ?= pasadena

# The Python environment lives in pipeline/.venv.nosync instead of .venv.
# ".nosync" stops iCloud Drive from syncing it; iCloud marks files in synced
# dot-folders as hidden, and Python skips hidden .pth files, which breaks imports.
export UV_PROJECT_ENVIRONMENT := .venv.nosync
UV ?= uv
RUN = cd pipeline && $(UV) run

.PHONY: all download clean test exercise setup

setup:
	cd pipeline && $(UV) sync

download:
	$(RUN) python -m zce download $(CITY)

clean:
	$(RUN) python -m zce clean $(CITY)

all: download clean

test:
	$(RUN) pytest

exercise:
	$(RUN) pytest -m exercise -v
