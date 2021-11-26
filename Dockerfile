FROM python:3.9-slim-bullseye
# Setup user junk
RUN groupadd -g 999 worker && \
    useradd -r -u 999 -g worker worker
RUN mkdir /home/worker
RUN chown -R worker:worker /home/worker
USER worker
ENV PATH=${PATH}:/home/worker/.local/bin

# App stuff
WORKDIR /home/worker
COPY /app ${HOME}
COPY pyproject.toml ${HOME}
ENV PYTHONPATH=${PYTHONPATH}:${PWD} 
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
ENTRYPOINT ["./docker-entrypoint.sh"]
