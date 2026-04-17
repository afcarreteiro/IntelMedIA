FROM pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ASR_MODEL_ID=Qwen/Qwen3-ASR-1.7B
ENV ASR_GPU_MEMORY_UTILIZATION=0.8
ENV ASR_MAX_NEW_TOKENS=64
ENV ASR_UNFIXED_CHUNK_NUM=2
ENV ASR_UNFIXED_TOKEN_NUM=5
ENV ASR_STREAM_CHUNK_SIZE_SEC=2.0

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/requirements.txt

COPY asr_qwen3_ws.py /app/asr_qwen3_ws.py

EXPOSE 8000

ENTRYPOINT ["python", "/app/asr_qwen3_ws.py"]
