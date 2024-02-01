FROM public.ecr.aws/lambda/python:3.11

COPY ./requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt
COPY ./src ${LAMBDA_TASK_ROOT}/src
CMD ["src.lambda_function.handler"]
