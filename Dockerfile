FROM python:3

WORKDIR /opt
ENV PYTHONPATH=/opt

RUN pip3 install --upgrade pip

COPY requirements.txt requirements.txt


RUN pip3 install --requirement /opt/requirements.txt;

COPY . .

ENTRYPOINT [ "python3", "run.py" ]
