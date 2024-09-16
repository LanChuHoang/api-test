FROM python:3.11.8

WORKDIR /code

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r ./requirements.txt

COPY . .

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
