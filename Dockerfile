FROM python:3.9
RUN pip install markdown html5lib numpy graphviz markupsafe==2.0.1
WORKDIR /app