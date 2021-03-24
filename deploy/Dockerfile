FROM public.ecr.aws/lambda/python:3.8

COPY pip_requirements.txt /pip_requirements.txt
RUN pip install -r /pip_requirements.txt

ADD posts/common/ ./common
ADD posts/models/ ./models
COPY posts/lambda_functions/* ./

# Don't specify an entrypoint here, it will be done in the SAM template.yaml