# Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: CC0-1.0

# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@uv run --no-dev --group docs $(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@uv run --no-dev --group docs $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


# Auto-generate API documentation
apidoc:
	uv run --no-dev --group docs sphinx-apidoc --module-first --output-dir source/code --force ..

clean-apidoc:
	rm -rfv source/code

.PHONY: apidoc clean-apidoc
clean: clean-apidoc

.PHONY: serve
html: apidoc
serve: html
	cd build/html && exec python -m http.server --bind 127.0.0.1
