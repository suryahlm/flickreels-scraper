# Cover Image Issue - Root Cause Analysis & Permanent Fix

## Tanggal: 4 Feb 2026

## Masalah
Cover image di app menampilkan gambar dari drama yang **salah** (segment video atau poster drama lain).

## Root Cause Analysis

### Bug 1: Scraper Metadata Corruption (FIXED)
- Pada run scraper sebelumnya, field `cover_r2` di `metadata.json` menyimpan path cover dari drama **lain**
- Contoh: Drama "CEO itu Ayah Anakku" punya `cover_r2: flickreels/Nenek Muda.../cover.png`
- Penyebab: Variabel `r2_cover_path` tidak di-reset dengan benar dalam loop concurrent

### Bug 2: Aggressive Image Caching
- Expo Image menggunakan `cachePolicy="memory-disk"` yang menyimpan gambar berdasarkan URL
- Setelah cover diperbaiki di server, app masih menampilkan gambar lama dari cache

## Solusi yang Diterapkan

### 1. Fix Data di R2 & Supabase ✅
Script `fix_covers_with_api.py`:
- Fetch cover URL **langsung dari API asli** (dengan HMAC signing)
- Download fresh cover image
- Upload ke **lokasi folder yang benar** di R2
- Update `thumbnail_url` di Supabase dengan URL yang benar (termasuk extension yang benar: .jpg/.png/.webp)

### 2. Cache Busting di App ✅
File: `lib/r2DramaService.ts`
```typescript
function addVersionParam(url: string): string {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}v=4`; // Increment when covers change
}
```
- Setiap kali ada fix cover, increment version number
- Ini memaksa Expo Image men-download gambar baru

### 3. Scraper Validation (RECOMMENDED)
Untuk mencegah masalah di masa depan, tambahkan validasi di scraper:
```python
# Setelah upload cover, validasi path
if r2_cover_path:
    # Pastikan path ada drama ID yang sedang diproses
    if f"({drama_id})" not in r2_cover_path:
        logger.error(f"CRITICAL: r2_cover_path mismatch! Expected drama {drama_id}, got {r2_cover_path}")
        r2_cover_path = ""  # Reset to prevent bad data
```

## Troubleshooting Steps (Untuk Masa Depan)

1. **Check Supabase thumbnail_url**:
   ```python
   requests.get(f"{SUPABASE_URL}/rest/v1/dramas?flickreels_id=eq.{ID}&select=thumbnail_url")
   ```

2. **Check R2 cover files**:
   ```python
   s3.list_objects_v2(Bucket='asiandrama-cdn', Prefix=f'flickreels/{folder}/cover')
   ```

3. **Test Railway stream URL**:
   ```python
   requests.head(f"https://...railway.app/api/stream/flickreels/{folder}/cover.{ext}")
   ```

4. **Clear app cache**:
   - Terminal Expo: tekan `Shift + R`
   - Atau Settings → Apps → Clear Cache

5. **Increment cache version** di `r2DramaService.ts` jika cover URL sama tapi gambar berubah

## Files Modified

1. `lib/r2DramaService.ts` - Cache version bumped to v4
2. `fix_covers_with_api.py` - Script untuk fix cover dari API asli  
3. `fix_menikah_cover.py` - Script khusus untuk 1 drama

## Prevention

1. **Selalu gunakan Supabase `thumbnail_url`** - jangan hardcode extension .jpg
2. **Scraper harus upload cover ke folder yang SAMA dengan drama** - validasi path
3. **Increment cache version** setiap ada bulk cover update
