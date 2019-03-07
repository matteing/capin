.PHONY: all install run

all: install run

install:
		pip install requests requests_html
		chmod +x ./capin.py

run:
		./capin.py
