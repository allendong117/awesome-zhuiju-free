FROM python:3.12-alpine
WORKDIR /app
COPY integrations/chatgpt/resource_api.py /app/resource_api.py
ENV PORT=8787
EXPOSE 8787
USER 65534:65534
CMD ["python", "/app/resource_api.py"]
