all: html pdf deploy

docs:
	make html && make pdf
	
deploy: html commit
	git subtree push --prefix docs/build/html origin gh-pages

commit: 
	git commit -am 'docs deploy'

html:
	cd docs && make html

apidocs:
	sphinx-apidoc -o docs/source . secrets.py sandbox.py old_stuff.py

pdf:
	cd docs && make latexpdf

watch:
	watchman watch docs; watchman -- trigger docs build -- make html 
