FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -m nltk.downloader punkt stopwords wordnet

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${API_PORT}"]