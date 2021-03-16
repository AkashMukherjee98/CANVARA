# Canvara Prototype
## Prerequisites
* Python 3.8
* Permissions to create, update and invoke Lambda functions in the Canvara AWS account

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

## Create AWS Lambda Functions (if needed)
NB: These commands are listed here for posterity. Eventually there should be deployment scripts doing all this automatically.

### create_post
First create the zip file to upload:
```
rm $CANVARA_ROOT/prototype/build/create_post.zip
cd $CANVARA_ROOT/prototype/.venv/canvara/lib/python3.8/site-packages/
zip -r $CANVARA_ROOT/prototype/build/create_post.zip .
cd $CANVARA_ROOT/prototype/posts/
zip -g $CANVARA_ROOT/prototype/build/create_post.zip -r models/
cd $CANVARA_ROOT/prototype/posts/lambda_functions
zip -g $CANVARA_ROOT/prototype/build/create_post.zip create_post.py
```

Then create the Lambda function:
```
cd $CANVARA_ROOT/prototype/build/
aws lambda create-function --function-name create_post --zip-file fileb://create_post.zip --handler create_post.lambda_handler --runtime python3.8 --role arn:aws:iam::423429615815:role/service-role/lambda_basic_execution
```

## Update AWS Lambda Functions
First, create the zip file to upload just like above.
Then, update the Lambda function:
```
cd $CANVARA_ROOT/prototype/build/
aws lambda update-function-code --function-name create_post --zip-file fileb://create_post.zip
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