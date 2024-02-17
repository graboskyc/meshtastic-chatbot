FROM python:3

WORKDIR /usr/src/app
COPY ./test.py ./
COPY ./requirements.txt ./

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD ["python", "test.py"]