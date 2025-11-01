# Celery CRM Weekly Report

This sets up a Celery task that runs weekly to generate a CRM report via GraphQL and logs to /tmp/crm_report_log.txt.

## Prerequisites
- Python 3.10+
- Redis running on localhost:6379

On Windows, you can run Redis via Docker:
- docker run --name redis -p 6379:6379 -d redis:7

## Install dependencies
- python -m pip install -r ..\requirements.txt

## Migrate database
- python ..\manage.py migrate

## Run services
- Start Celery worker:
  - celery -A crm worker -l info
- Start Celery Beat:
  - celery -A crm beat -l info

Keep your Django server running as usual:
- python ..\manage.py runserver

## Verify
- Wait until Monday 06:00 server time or trigger manually:
  - python ..\manage.py shell -c "from crm.tasks import generate_crm_report; print(generate_crm_report.delay())"
- Check the log file:
  - Windows: C:\tmp\crm_report_log.txt
  - Linux/macOS: /tmp/crm_report_log.txt