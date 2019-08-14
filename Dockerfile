FROM python:3.7-alpine3.9
RUN apk add --no-cache build-base libffi-dev
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
COPY cmtg /app/cmtg
ENTRYPOINT [ "python", "-m", "cmtg" ]