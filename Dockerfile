FROM python:3.9-slim-buster

LABEL org.label-schema.name="Babylon"
LABEL org.label-schema.description="Babylon is a tool designed to simplify interaction between Cosmo Tech solutions and the Azure environment."
LABEL org.label-schema.url="https://github.com/Cosmo-Tech/Babylon"
LABEL org.label-schema.maintainer="alexis.fossart@cosmotech.com"
LABEL org.label-schema.docker.cmd="docker run -it --rm --mount type=bind,source="$(pwd)"/config,target=/opt/babylon/config babylon"

# Install external programs
RUN apt-get update && apt-get install -y curl apt-transport-https

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Docker
RUN curl https://download.docker.com/linux/static/stable/x86_64/docker-20.10.9.tgz > docker.tgz
RUN tar xzvf docker.tgz
RUN cp docker/* /usr/bin/

# Install kubectl
RUN curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list
RUN apt-get update && apt-get install -y kubectl

# Install Babylon
COPY . /app
WORKDIR /app/
RUN pip install .
RUN echo 'eval "$(_BABYLON_COMPLETE=bash_source babylon)"' >> ~/.bashrc
ENV BABYLON_CONFIG_DIRECTORY=/opt/babylon/config

ENTRYPOINT ["bash"]