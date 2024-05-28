FROM python:3.12
EXPOSE 8501
WORKDIR /sample-app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["streamlit", "run", "Home.py"]