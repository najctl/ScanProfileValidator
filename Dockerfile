# Optional local runner; the Python CLI remains usable without Docker.
FROM python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app.py validator.py diagnostics.py ./
COPY inputs/ ./inputs/
COPY tests/app_test.py ./tests/app_test.py

# A numeric UID/GID avoids creating accounts or installing extra packages.
USER 10001:10001

# Run the existing suite during the build; no additional test cases are added.
RUN python -m unittest discover -s tests -p "*_test.py" -v

ENTRYPOINT ["python", "app.py"]
CMD ["--input", "inputs/primary.json"]
