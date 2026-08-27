# Edutech AI Worker

Worker asynchronous untuk fitur AI MVP Edutech:

- tutor/chat pembelajaran;
- analisis laporan performa;
- rekomendasi belajar.

## Alur

```text
backend -> POST /v1/jobs -> Redis -> Celery worker -> OpenAI Responses API
                |
backend <- GET /v1/jobs/{id} <- Redis result backend
```

FastAPI hanya menerima dan membaca status job. Panggilan OpenAI terjadi di Celery worker,
sehingga request backend tidak tertahan selama model memproses jawaban.
Worker memakai late acknowledgement, satu prefetch per process, retry dengan backoff, dan
time limit agar job yang macet atau worker yang mati dapat dipulihkan dengan aman.

## Menjalankan dengan Docker

```bash
cp .env.example .env
```

Isi `OPENAI_API_KEY` pada `.env`, kemudian:

```bash
docker compose up --build
```

Dokumentasi interaktif tersedia di `http://localhost:8000/docs`.

## Menjalankan secara lokal

Python 3.11 atau lebih baru dan Redis diperlukan.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
python -m ai_worker
```

Pada terminal lain, jalankan worker:

```bash
celery --app ai_worker.celery_app:celery_app worker --loglevel=INFO --queues=ai_jobs
```

Jika Redis berjalan di host, ubah kedua URL Redis di `.env` dari hostname `redis`
menjadi `localhost`.

## Mengirim job

Semua kemampuan memakai satu interface `POST /v1/jobs` dengan field `type` sebagai
discriminator.

Tutor:

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "tutor",
    "user_id": "student-123",
    "subject": "Matematika",
    "education_level": "SMP",
    "message": "Jelaskan persamaan linear dengan contoh sederhana"
  }'
```

Analisis laporan:

```json
{
  "type": "report_analysis",
  "user_id": "student-123",
  "report_title": "Performa Semester 1",
  "performance_data": {
    "matematika": 72,
    "bahasa_indonesia": 86,
    "attendance_percent": 94
  },
  "notes": "Nilai matematika tiga minggu terakhir mulai meningkat."
}
```

Rekomendasi belajar:

```json
{
  "type": "learning_recommendation",
  "user_id": "student-123",
  "performance_summary": "Kuat di geometri, masih kesulitan pada aljabar dasar.",
  "learning_goal": "Mencapai nilai matematika minimal 80.",
  "preferences": ["video singkat", "latihan bertahap"]
}
```

Respons penerimaan job:

```json
{"job_id": "c3a...", "status": "queued"}
```

Cek hasilnya melalui `GET /v1/jobs/{job_id}`. Status yang mungkin adalah `queued`,
`processing`, `retrying`, `succeeded`, dan `failed`.

## Pemeriksaan dan test

```bash
ruff check .
ruff format --check .
pytest --cov=ai_worker
```

## Catatan keamanan MVP

- Jangan memasukkan API key ke Git; `.env` sudah diabaikan.
- Hindari mengirim data pribadi yang tidak diperlukan ke model.
- `user_id` dipakai untuk korelasi internal dan tidak dimasukkan ke prompt OpenAI.
- Endpoint ini sebaiknya hanya dapat diakses oleh backend internal atau API gateway.
- Hasil AI adalah bantuan belajar, bukan satu-satunya dasar penilaian siswa.

Integrasi menggunakan Responses API dan structured JSON output supaya hasil dari model
divalidasi sebelum dikembalikan ke backend. Model dapat diganti melalui `OPENAI_MODEL`.
