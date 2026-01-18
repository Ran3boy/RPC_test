FROM python:3.11-slim

WORKDIR /service

COPY protobufs/ /service/protobufs/
COPY glossary_service/ /service/glossary_service/

WORKDIR /service/glossary_service

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m grpc_tools.protoc -I../protobufs \
        --python_out=. --grpc_python_out=. ../protobufs/glossary.proto

ENV GRPC_PORT=50051
ENV DATA_PATH=/data/terms.json

VOLUME ["/data"]
EXPOSE 50051

ENTRYPOINT ["python", "server.py"]
