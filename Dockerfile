FROM python:3.9
RUN pip install markdown numpy graphviz 
WORKDIR /app