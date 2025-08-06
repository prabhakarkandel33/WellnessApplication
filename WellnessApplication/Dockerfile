FROM python:3.10-slim

ENV PYTHONDOWNWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /wellnessapp

COPY requirements.txt /wellnessapp/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /wellnessapp/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
