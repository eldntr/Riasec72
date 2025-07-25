# Gunakan image Python yang ringan
FROM python:3.11-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Salin file requirements jika ada, install Flask
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir flask

# Salin semua file aplikasi ke dalam container
COPY . .

# Expose port Flask
EXPOSE 5000

# Jalankan aplikasi Flask dengan auto-reload (development mode)
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
