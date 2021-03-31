# Canvara Prototype
## Prerequisites
* Python 3.8
* Permissions to create, update and invoke Lambda functions in the Canvara AWS account
* [AWS SAM CLI](https://docs.amazonaws.cn/en_us/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) (required for deployment)
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) (optional)

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

## Deploy AWS Lambda Functions
To simplify our development and deployment, we deploy the Lambda functions as container images using [AWS SAM](https://aws.amazon.com/serverless/sam/). For now, there is a simple container image which contains all the functions and their dependencies.

### Build the application
```
cd $CANVARA_ROOT/prototype
sam build
```

### Deploy the application
```
cd $CANVARA_ROOT/prototype
sam deploy --image-repository 423429615815.dkr.ecr.us-west-2.amazonaws.com/canvara
```

## Invoke AWS Lambda Functions
In all of the following examples, replace the values in payload as desired. Replace `/dev/stdout` with any output filename as desired.

### create_post
```
aws lambda invoke --cli-binary-format raw-in-base64-out --function-name create_post --payload='{ "customer_id": "1", "post": {"summary": "Task summary", "description": "Task details"}}' /dev/stdout
```

### list_posts
```
aws lambda invoke --cli-binary-format raw-in-base64-out --function-name list_posts --payload='{ "customer_id": "1"}' /dev/stdout
```

### Pretty-print the Response
The output from Lambda can be pretty printed using a handy python module.
```
aws lambda invoke --cli-binary-format raw-in-base64-out --function-name list_posts --payload='{ "customer_id": "1"}' response.json && python3 -m json.tool response.json
```