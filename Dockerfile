FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["bash", "-c", "python manage.py migrate && gunicorn cac_project.wsgi --bind 0.0.0.0:$PORT"]