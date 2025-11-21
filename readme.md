Personal programming task test preperation library for Latvian Informatics Olympiad (LIO).

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

See example in `./examples/usage/script.py`.

## Latvian informatics olympiad

LIO has its own task file structure and a more granular point distribution system.
Besides having subtasks, LIO has testgroups. User score is accumulated over testgroups.

See `./examples/task.yaml` for example of how points are assigned to testgroups and testgroups are assigned to subtasks.

Tests are named like `task.i01a`, `task.i01b`, `task.i01c`, etc. Text `task` is replaced by the identifier of the task.
Number `01` is the testgroup number. Letter `a` is the testcase number inside the testgroup.

If the testfile is an answer not an input, the name is `task.o01a`. The `i` is replaced by `o`.

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