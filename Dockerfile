FROM python:3.11-slim

# Install uv (static binary, no pip needed).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# The container has no .git, so hatch-vcs cannot derive a version from tags.
# Pin a placeholder: the version is irrelevant for running tests and lint.
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app
COPY pyproject.toml uv.lock README_pypi.md LICENSE.txt ./
COPY ./ipytv ./ipytv
COPY ./tests ./tests
COPY ./scripts ./scripts

RUN uv sync --frozen

RUN ln -s /app/scripts/test.sh /usr/bin/runtest && \
    ln -s /app/scripts/lint.sh /usr/bin/runlint

ENTRYPOINT [ "/app/scripts/test.sh" ]
