# Zoning Capacity Explorer: one command per pipeline step.
#   make all CITY=pasadena     download + clean + capacity + export (website data)
#   make test                  unit tests
#   make exercise              tests for the current learning exercise

CITY ?= pasadena

# The Python environment lives in pipeline/.venv.nosync instead of .venv.
# ".nosync" stops iCloud Drive from syncing it; iCloud marks files in synced
# dot-folders as hidden, and Python skips hidden .pth files, which breaks imports.
export UV_PROJECT_ENVIRONMENT := .venv.nosync
UV ?= uv
RUN = cd pipeline && $(UV) run

.PHONY: all download clean capacity export golden test test-web exercise setup

setup:
	cd pipeline && $(UV) sync

download:
	$(RUN) python -m zce download $(CITY)

clean:
	$(RUN) python -m zce clean $(CITY)

capacity:
	$(RUN) python -m zce capacity $(CITY)

export:
	$(RUN) python -m zce export $(CITY)

golden:
	$(RUN) python -m zce golden $(CITY)

all: download clean capacity export golden

test:
	$(RUN) pytest
	cd web && npx vitest run

exercise:
	$(RUN) pytest -m exercise -v
