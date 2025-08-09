# this is builder's environment
# in this container, some package will be built
FROM python:3.12 AS builder

# build in working dir according to Pipfile
WORKDIR /usr/src/app

# copy Pipfile
#COPY Pipfile Pipfile.lock /usr/src/app/
#RUN pip install pipenv \
#    && pipenv install --system
COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt

# this is produce environment
# to decrease container size, use slim image
FROM python:3.12-slim

WORKDIR /usr/src/app

# python don't use buffer for standard output
#ENV PIPENV_VENV_IN_PROJECT=1
ENV PYTHONUNBUFFERED=1

# copy built packages from builder's environment
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
#COPY --from=builder /usr/local/bin /usr/local/bin

# copy script files
COPY . ./

CMD ["python", "main.py"]
