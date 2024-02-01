FROM python:slim

WORKDIR /opt/minecraft-skinpack-generator/test-client
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY ./src ./src
CMD ["python", "src/main.py"]
