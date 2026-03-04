FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY application ./application

# Streamlit runtime settings
EXPOSE 8501
VOLUME ["/app/application/model/reflections"]

CMD ["streamlit", "run", "application/view/analysis_UI/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
