FROM python:3.9-slim-buster
WORKDIR /app/
COPY . /app
RUN pip install .
COPY Babylon/templates/config_template /opt/babylon/config/
ENTRYPOINT ["bash"]