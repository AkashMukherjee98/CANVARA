# Canvara Backend
## Prerequisites
* Python 3.8

## Setup Environment Variables
| Environment Variable | Description|
|-|-|
| PYTHONPATH | (**system variable**) Search path for Python modules. Typically set to `$PYTHONPATH:/path/to/canvara/backend/src` |
| COGNITO_REGION | AWS Region for the Cognito user pool |
| COGNITO_USERPOOL_ID | Cognito user pool used for authentication |
| COGNITO_APP_CLIENT_ID | Cognito app client id |
| S3_USER_UPLOADS_BUCKET | S3 bucket where the user uploads (images, videos) should be stored |
| POSTGRES_USERNAME | Username for connecting to the postgres database. E.g. `postgres` |
| POSTGRES_PASSWORD | Password for connecting to the postgres database |
| POSTGRES_HOST | Hostname of the postgres database |
| POSTGRES_PORT | Port of the postgres database. E.g. `5432` |
| POSTGRES_DATABASE | Name of the Canvara database. e.g. `postgres` |

### (Optional) Set environment variables using .env file
Instead of setting the environment variables manually, they can be managed using a .env file. Create a `.env` file using the existing `.env.example` file and make necessary changes.

```
cp .env.example .env
<update .env>
export $(cat .env | xargs)
```

## Setup Python Virtual Environment
### Create Virtual Environment
```
python3 -m venv .venv/canvara
source .venv/canvara/bin/activate
```

### Install Python dependencies
```
pip install -r pip_requirements.txt
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
cd src
FLASK_APP=backend flask run
```

### Run locally using Gunicorn
```
cd src
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
