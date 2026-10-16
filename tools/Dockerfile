# Tools image: publishes project folders (tools/projects.py) and runs the
# webmaster panel (tools/admin.py). Built by GitHub Actions and published as
# ghcr.io/rafierosliputra/johorstudio-tools:latest
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory '*'
RUN pip install --no-cache-dir "pillow>=10,<12" && (pip install --no-cache-dir pillow-heif || true)
WORKDIR /work
ENTRYPOINT ["python"]
CMD ["tools/projects.py"]
