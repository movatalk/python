genexecutable:
	cp main.py movatalk
	sed  -i '1i #!/usr/bin/python\n' movatalk

install: genexecutable
	sudo cp movatalk /usr/bin/
	sudo chmod +x /usr/bin/movatalk
	rm movatalk