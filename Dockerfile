ARG IMAGE=intersystemsdc/irishealth-community:latest
FROM $IMAGE AS builder

ENV PYTHONUTF8=1

WORKDIR /home/irisowner/irisdev
#RUN chown ${ISC_PACKAGE_MGRUSER}:${ISC_PACKAGE_IRISGROUP} /opt/irisapp

USER root
RUN /usr/irissys/bin/irispython -m pip install --target /usr/irissys/mgr/python --no-cache-dir intersystems-irispython requests && \
    chown -R ${ISC_PACKAGE_MGRUSER}:${ISC_PACKAGE_IRISGROUP} /usr/irissys/mgr/python
USER ${ISC_PACKAGE_MGRUSER}

# copy all the source into container and run iris. also run a initial script
RUN --mount=type=bind,src=.,dst=. \
    iris start IRIS && \
    iris merge IRIS merge.cpf && \
	iris session IRIS < iris.script && \
    iris stop IRIS quietly


FROM $IMAGE AS final

ENV PYTHONUTF8=1

ADD --chown=${ISC_PACKAGE_MGRUSER}:${ISC_PACKAGE_IRISGROUP} https://github.com/grongierisc/iris-docker-multi-stage-script/releases/latest/download/copy-data.py /irisdev/app/copy-data.py

RUN --mount=type=bind,source=/,target=/builder/root,from=builder \
    cp -f /builder/root/usr/irissys/iris.cpf /usr/irissys/iris.cpf && \
    python3 /irisdev/app/copy-data.py -c /usr/irissys/iris.cpf -d /builder/root/