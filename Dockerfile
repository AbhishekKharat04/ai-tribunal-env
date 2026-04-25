FROM python:3.10-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user server/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gradio

COPY --chown=user . /app

ENV PORT=7860
ENV TASK_LEVEL=1

EXPOSE 7860

# Mount FastAPI at /api, Gradio as main UI
CMD ["python", "gradio_ui.py"]
