# Usa l'immagine base già costruita
FROM base AS web

WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "threatlinker.wsgi:application"]
