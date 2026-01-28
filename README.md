# FlickReels R2 Scraper

Scraper untuk download drama FlickReels dan upload ke Cloudflare R2.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Test connection
python flickreels_r2_scraper.py --mode=test

# Scrape metadata only
python flickreels_r2_scraper.py --mode=metadata

# Full scrape
python flickreels_r2_scraper.py --mode=full
```

### 4-Day Batch Scraping (Recommended)

Untuk menghindari blocking, gunakan batch scraping:

```bash
# Hari 1: Batch 1 (~594 dramas, ~2-3 jam)
python flickreels_r2_scraper.py --mode=full --batch=1

# Hari 2: Batch 2 (~594 dramas, ~2-3 jam)
python flickreels_r2_scraper.py --mode=full --batch=2

# Hari 3: Batch 3 (~594 dramas, ~2-3 jam)
python flickreels_r2_scraper.py --mode=full --batch=3

# Hari 4: Batch 4 (~594 dramas, ~2-3 jam)
python flickreels_r2_scraper.py --mode=full --batch=4
```

| Batch | Dramas | Estimasi Waktu |
|-------|--------|----------------|
| 1 | ~594 | 2-3 jam |
| 2 | ~594 | 2-3 jam |
| 3 | ~594 | 2-3 jam |
| 4 | ~594 | 2-3 jam |

1. **Create New Project** di [Railway](https://railway.app)

2. **Connect GitHub** atau upload folder ini

3. **Add Environment Variables** (dari `.env.example`):
   ```
   R2_ACCOUNT_ID=caa84fe6b1be065cda3836f0dac4b509
   R2_ACCESS_KEY_ID=a4903ea93c248388b6e295d6cdbc8617
   R2_SECRET_ACCESS_KEY=5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9
   R2_BUCKET_NAME=asiandrama-cdn
   FLICKREELS_TOKEN=eyJ0eXAi...
   ```

4. **Deploy** - Railway akan auto-detect Python dan run scraper

### Scheduled Scraping (Cron Job)

Untuk auto-scraping setiap hari, buat **Cron Job** di Railway:

1. Go to Project Settings
2. Add Cron Job
3. Schedule: `0 2 * * *` (setiap jam 2 pagi UTC)
4. Command: `python flickreels_r2_scraper.py --mode=full`

## Files

| File | Description |
|------|-------------|
| `flickreels_r2_scraper.py` | Main scraper |
| `flickreels_scraper.py` | Original scraper (tanpa R2) |
| `sign_generator.py` | Standalone sign generator |
| `API_DOCUMENTATION.md` | API reference |
| `all_dramas.json` | Drama database (2,376 dramas) |

## API Documentation

Lihat [API_DOCUMENTATION.md](API_DOCUMENTATION.md) untuk detail lengkap.

### Key Points

- **Secret Key**: `tsM5SnqFayhX7c2HfRxm`
- **Algorithm**: HmacSHA256
- **Total Dramas**: 2,376
- **VIP Required**: Yes, untuk streaming

## Troubleshooting

### Sign Error
```
Check boolean casing - Python True/False vs Java true/false
```

### Token Expired/Banned
```
1. Buka FlickReels di emulator dengan HTTP Toolkit
2. Login dengan akun VIP
3. Capture request apapun
4. Copy token baru dari header
5. Update FLICKREELS_TOKEN di Railway
```

### R2 Upload Failed
```
Check R2 credentials di Railway Variables
```

## License

Private - Internal use only
