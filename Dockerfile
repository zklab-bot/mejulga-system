FROM python:3.11-slim
WORKDIR /app/content-engine
COPY content-engine/ .
RUN pip install --no-cache-dir fastapi uvicorn anthropic requests python-dotenv apscheduler
EXPOSE 8000
CMD ["uvicorn", "webhook.server:app", "--host", "0.0.0.0", "--port", "8000"]
