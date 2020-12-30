FROM martinobrink/ikea-homelight-baseimage:latest

COPY ./app.py /usr/src/app/
COPY ./tradfri_standalone_psk.conf /usr/src/app/

WORKDIR /usr/src/app

ENTRYPOINT python3 app.py