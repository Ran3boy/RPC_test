FROM python:3.11-slim

WORKDIR /service

COPY protobufs/ /service/protobufs/
COPY web_gateway/ /service/web_gateway/

WORKDIR /service/web_gateway

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m grpc_tools.protoc -I../protobufs \
        --python_out=. --grpc_python_out=. ../protobufs/glossary.proto

ENV HOST=0.0.0.0
ENV PORT=8000
ENV GLOSSARY_HOST=glossary
ENV GLOSSARY_PORT=50051

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
