# prepare the builder image
FROM python:3.8-slim as builder
COPY . /code

# setup virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PIP_DISABLE_PIP_VERSION_CHECK=1

# install dependencies and the actual package
RUN pip install wheel && pip install -r /code/requirements.txt && pip install /code

# prepare the runtime image
FROM python:3.8-slim as runtime
ENV PYTHONBUFFERED=1 PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
CMD ["neighbour-seeker"]
