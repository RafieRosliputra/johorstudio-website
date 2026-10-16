# Image for "docker compose run --rm publish": turns project folders into web pages.
FROM python:3.12-slim
RUN pip install --no-cache-dir "pillow>=10,<12" && (pip install --no-cache-dir pillow-heif || true)
WORKDIR /work
ENTRYPOINT ["python", "tools/projects.py"]
