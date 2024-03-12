FROM python:3 as s1

LABEL org.label-schema.name="Babylon"
LABEL org.label-schema.description="Babylon is a tool designed to simplify interaction between Cosmo Tech solutions and the Azure environment."
LABEL org.label-schema.url="https://github.com/Cosmo-Tech/Babylon"
LABEL org.label-schema.maintainer="nibaldo.donoso@cosmotech.com"
RUN apt update;apt install -y curl apt-transport-https 

# Install Azure CLI
FROM s1 as s2
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Docker
FROM s2 as s3
RUN curl https://download.docker.com/linux/static/stable/x86_64/docker-20.10.9.tgz > docker.tgz
RUN tar xzvf docker.tgz
RUN cp docker/* /usr/bin/

# Install Babylon
FROM s3
WORKDIR /app
COPY . .
RUN pip install .

ENTRYPOINT ["bash"]