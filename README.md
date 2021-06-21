# Canvara Prototype
## Prerequisites
* Python 3.8

## Setup Environment Variables
```
export CANVARA_ROOT=~/src/canvara
```

## Setup Python Virtual Environment
```
cd $CANVARA_ROOT/prototype
python3 -m venv .venv/canvara
source .venv/canvara/bin/activate
```

## Install Python dependencies
```
pip install -r $CANVARA_ROOT/prototype/backend/pip_requirements.txt
```

### Run the Flask app locally
```
cd $CANVARA_ROOT/prototype/backend/src
FLASK_APP=app.py flask run
```
