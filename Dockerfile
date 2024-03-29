FROM python:3.8.15-buster
COPY ./requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python --version
CMD ["bash"]