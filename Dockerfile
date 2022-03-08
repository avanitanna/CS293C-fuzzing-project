FROM python:3.9
RUN pip install markdown numpy graphviz markupsafe==2.0.1
WORKDIR /app