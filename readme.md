Personal test preperation library for Latvian Informatics Olympiad (LIO).
Context is competitive programming tasks.

## Installation

Library requires IOI "[isolate](https://github.com/ioi/isolate)" sandbox.
Isolate is used for safely and precisely measuring execution time and memory.
See "isolate sandbox installation" section below for installation instructions.

Otherwise, you can install the library in editable mode using pip:
```bash
python -m pip install -e .
```

Editable mode allows to edit the library code and see changes without reinstalling.

## Usage instructions

See example in `./example/usage/script.py`.

## Latvian informatics olympiad

We have our own 

## Isolate sandbox installation

Installation is approximately as follows.
Dont blindly copy and paste, these are meant as guidelines.

```bash
Approximate installation instructions
git clone https://github.com/ioi/isolate.git
cd isolate
make
sudo make install
cd systemd
sudo cp isolate.service /etc/systemd/system/
sudo cp isolate.slice /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable isolate.service
sudo systemctl start isolate.service
sudo systemctl restart isolate.service
isolate-check-environment
isolate --cg --init
```