# Canvara Prototype
## Prerequisites
* Python 3.8

## Setup Environment Variables
| Environment Variable | Description|
|-|-|
| CANVARA_ROOT | Root directory of the backend repository. Helpeful for defining the other environment variables. |
| CANVARA_CONFIGS_DIR | Path to the `configs` directory. Typically set to `$CANVARA_ROOT/configs` |
| CANVARA_ENV | Current Canvara environment, e.g. local, production, ci etc. Config files for the current environment are expected to be in `$CANVARA_CONFIGS_DIR/$CANVARA_ENV` directory |
| PYTHONPATH | (**system variable**) Search path for Python modules. Typically set to `$PYTHONPATH:$CANVARA_ROOT/src` |

Example:
```
export CANVARA_ROOT=~/src/canvara/prototype
export CANVARA_CONFIGS_DIR=$CANVARA_ROOT/configs
export CANVARA_ENV=local
export PYTHONPATH=$PYTHONPATH:$CANVARA_ROOT/src
```

## Setup Python Virtual Environment
```
cd $CANVARA_ROOT
python3 -m venv .venv/canvara
source .venv/canvara/bin/activate
```

## Install Python dependencies
```
pip install -r $CANVARA_ROOT/pip_requirements.txt
```

## Run the application
When running on your dev machine, the application can be run using Flask or Gunicorn. In Production, we will use Gunicorn only.
### Run locally using Flask
```
cd $CANVARA_ROOT/src
FLASK_APP=backend flask run
```
### Run locally using Gunicorn
```
cd $CANVARA_ROOT/src
gunicorn backend:app
```
