FROM ubuntu:latest
COPY ./requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python --version
CMD ["bash"]