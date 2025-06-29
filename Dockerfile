FROM python:3.10 AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .



FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /app .

EXPOSE 5000
CMD ["python3", "main.py"]