# Immagine base Python
FROM python:3.11-slim

# Directory di lavoro nel container
WORKDIR /app

# Copia e installazione dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il codice sorgente
COPY . .

# Espone le porte per FastAPI (8000) e Streamlit (8501)
EXPOSE 8000 8501

# Comando predefinito per avviare l'API backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]