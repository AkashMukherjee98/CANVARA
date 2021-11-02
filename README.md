# Canvara Backend
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
### Create Virtual Environment
```
cd $CANVARA_ROOT
python3 -m venv .venv/canvara
source .venv/canvara/bin/activate
```

### Install Python dependencies
```
pip install -r $CANVARA_ROOT/pip_requirements.txt
```

## Setup database
### Install Postgres
Follow platform-specific steps - https://www.postgresql.org/download/

### Create/update your local Canvara config file
If you haven't done so already:
```
cp configs/local/canvara_config.yaml.example configs/local/canvara_config.yaml
```
Then update the database username, password, hostname and port as appropriate.

### Initialize the database
```
alembic -c src/backend/db/alembic.ini upgrade head
```

## Run the application
When running on your dev machine, the application can be run using Flask or Gunicorn. In Production, we use Gunicorn.

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

## Authentication
We use AWS Cognito for authenticiation, and the API expects a Bearer token in the Authorization header. For development purposes, you can get a token for your user by making a POST request to AWS Cognito. You can use curl, or Postman, or any other tool that lets you make an http request.

### Get a token using curl and jq
Replace `<username>`, `<password>`, and `<client_id>` with appropriate values.
```
curl --silent --request POST \
  --url https://cognito-idp.us-west-2.amazonaws.com/ \
  --header 'Content-Type: application/x-amz-json-1.1' \
  --header 'X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth' \
  --data '{"AuthParameters": {"USERNAME": "<username>", "PASSWORD": "<password>"}, "AuthFlow": "USER_PASSWORD_AUTH", "ClientId": "<client_id>"}' | jq '.AuthenticationResult.IdToken'
```

## Query the API
With the authentication token, you can now call the API. Here's an example of calling the user profile API using curl, but you can use your favorite tool.
```
curl --silent --request GET --url http://127.0.0.1:5000/users/me --header 'Authorization: Bearer <auth_token>'
```
