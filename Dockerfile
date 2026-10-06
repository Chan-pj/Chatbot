FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# CPU 전용 PyTorch (GPU 버전 대비 이미지 용량 대폭 감소)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

# 임베딩 모델을 이미지에 포함 (실행 시 다운로드 생략)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"

COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
