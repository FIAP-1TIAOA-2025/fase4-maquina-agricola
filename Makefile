SHELL := /bin/zsh

all: prep-venv clean

prep-venv: 
	python3 -m venv fase3_pio_env && source fase3_pio_env/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt  && /bin/zsh

clean:
	-/bin/rm -rf fase3_pio_env
