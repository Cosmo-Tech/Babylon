# Babylon API image: the same image runs the API (uvicorn) and the worker Jobs (python -m babylon_api.worker).
#
#   docker build -t babylon-api:dev .
#
# Two stages: the "build" stage has uv and compiles the virtualenv; the final stage only
# copies the virtualenv, so build tools are not shipped.

ARG BASE_IMAGE=registry.cosmotech.com/proxy-chainguard/cosmotech/python
ARG PYTHON_TAG=3.13

FROM ${BASE_IMAGE}:${PYTHON_TAG}-dev AS build
# Chainguard images run as "nonroot" (65532) by default: /opt and /src are not writable without root.
USER root
COPY --from=ghcr.io/astral-sh/uv:0.9.13 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python
WORKDIR /src
# 1. Dependencies only (cached layer: rebuilt only when the lock file changes).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --extra api --no-install-project
# 2. The project itself (not editable: the source folder is not copied to the final image).
COPY Babylon ./Babylon
COPY babylon_api ./babylon_api
RUN uv sync --locked --no-dev --extra api --no-editable


FROM ${BASE_IMAGE}:${PYTHON_TAG}-dev
ARG KUBECTL_VERSION=v1.36.4
ARG TARGETARCH=amd64
USER root
# Chainguard (Wolfi) uses apk, not apt-get. git is already in the -dev image.
# kubectl: Babylon reads workspace Job logs with `kubectl logs` (pinned version, downloaded from the official release).
RUN apk add --no-cache ca-certificates curl \
    && curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
    && chmod 0755 /usr/local/bin/kubectl \
    && apk del --no-cache curl

COPY --from=build /opt/venv /opt/venv
# Existing "nonroot" user of Chainguard images. Numeric: Kubernetes `runAsNonRoot: true` can only verify a numeric UID.
RUN mkdir -p /work && chown 65532:65532 /work
USER 65532
# Git sha of the build, shown by GET /about (docker build --build-arg BUILD=$(git rev-parse --short HEAD)).
ARG BUILD=""
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BABYLON_API_BUILD=${BUILD} \
    HOME=/work
WORKDIR /work
EXPOSE 8000
# The Chainguard python image has ENTRYPOINT ["/usr/bin/python"]: reset it, otherwise CMD becomes
# `python uvicorn ...` and `docker run <image> sh` becomes `python sh`.
ENTRYPOINT []
CMD ["uvicorn", "babylon_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
