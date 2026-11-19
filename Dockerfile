# Cosmo Tech Babylon API image: the same image runs the API (uvicorn) and the worker Jobs (python -m babylon_api.worker).
#
#   docker build --build-arg BUILD=$(git rev-parse --short HEAD) -t babylon-api:dev .
#
# Two stages: the "build" stage has uv and compiles the virtualenv; the final stage only
# copies the virtualenv, so build tools are not shipped.

FROM registry.cosmotech.com/proxy-chainguard/cosmotech/python:3.13-dev AS build
# -- Chainguard images run as "nonroot" (65532) by default: /opt and /src are not writable without root.
USER root
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_PYTHON=/usr/bin/python
WORKDIR /src
# -- Dependencies only (cached layer: rebuilt only when the lock file changes).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --extra api --no-install-project
# -- The project itself (not editable: the source folder is not copied to the final image).
COPY Babylon ./Babylon
COPY babylon_api ./babylon_api
RUN uv sync --locked --no-dev --extra api --no-editable


FROM registry.cosmotech.com/proxy-chainguard/cosmotech/python:3.13-dev
ARG TARGETARCH=amd64
USER root
# -- Install ca certificates and kubectl, git is already in the -dev image.
# -- kubectl: Babylon reads workspace Job logs with `kubectl logs`.
RUN apk add --no-cache ca-certificates kubectl-1.36
COPY --from=build /opt/venv /opt/venv
# -- Existing "nonroot" user of Chainguard images. Numeric: Kubernetes `runAsNonRoot: true` can only verify a numeric UID.
RUN mkdir -p /work && chown 65532:65532 /work
USER 65532
# -- Git sha of the build, shown by GET /about.
ARG BUILD=""
ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BABYLON_API_BUILD=${BUILD}
ENV HOME=/work
WORKDIR /work
EXPOSE 8000
# -- The Chainguard python image has ENTRYPOINT ["/usr/bin/python"]: reset it.
#    CMD [] becomes `python uvicorn ...` and `docker run <image> sh` becomes `python sh`.
ENTRYPOINT []
CMD ["uvicorn", "babylon_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
