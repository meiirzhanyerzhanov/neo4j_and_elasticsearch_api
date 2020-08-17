FROM python:3.7
ADD . /code
WORKDIR /code
#RUN apk update
#RUN apk add make automake gcc g++ subversion python3-dev
RUN pip3 install -r requirements.txt
CMD python neodb_api.py

