FROM martinobrink/ikea-homelight-baseimage:latest

COPY ./app.py /usr/src/app/
COPY ./tradfri_standalone_psk.conf /usr/src/app/
COPY ./requirements.txt /usr/src/app

RUN pip3 install -r /usr/src/app/requirements.txt

WORKDIR /usr/src/app

ENTRYPOINT python3 app.py