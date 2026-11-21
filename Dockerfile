FROM python:3.13-slim

WORKDIR /app
COPY . /app

# A container has to answer from outside its own loopback. Port 8080 matches
# the common PaaS default; PORT still wins when the platform sets it.
ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "serve.py"]
