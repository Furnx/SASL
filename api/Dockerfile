FROM python:3.14

RUN python3 -m pip install uv

WORKDIR /var/sasl_api

COPY . .

RUN uv sync && uv lock

EXPOSE 8443

CMD ["uv","run","main.py"]



