---
description: Download drama videos to local and upload to R2
---

# Drama Video Download & Upload Workflow

## PENTING - Folder Structure

**WAJIB**: Semua file untuk 1 drama harus dalam 1 folder dengan format:
```
Video Drama TS/[TANGGAL]/[Judul Drama] ([ID])/
├── metadata.json       ← Info drama
├── cover.jpg           ← Cover image  
├── ep_001.m3u8         ← Episode 1 manifest
├── ep_001_0000.ts      ← Episode 1 segment 0
├── ep_001_0001.ts      ← Episode 1 segment 1
├── ep_002.m3u8         ← Episode 2 manifest
└── ...
```

**JANGAN** simpan video di subfolder terpisah seperti `videos/[ID]/`

---

## Step 1: Download Videos

```bash
cd D:\Surya\IT\Test Scraping\FlickReels

# Download specific number of dramas
python download_videos.py --input "Scraping 01/[TANGGAL]/dramas.json" --output "Video Drama TS/[TANGGAL]" --max-dramas 5

# Download specific drama IDs
python download_videos.py --input "Scraping 01/[TANGGAL]/dramas.json" --output "Video Drama TS/[TANGGAL]" --drama-ids 2858,533,487
```

// turbo
## Step 2: Verify Folder Structure

```powershell
# Check each folder has all files (metadata + episodes)
Get-ChildItem -Directory "Video Drama TS/[TANGGAL]" | ForEach-Object { 
    $name = $_.Name
    $count = (Get-ChildItem $_.FullName -File).Count
    Write-Host "$name : $count files" 
}
```

## Step 3: Upload to R2

```bash
python upload_to_r2.py --input "Video Drama TS/[TANGGAL]"
```

---

## R2 Structure

Di R2, struktur folder adalah:
```
dramas/
├── Tak Bisa Melepasmu (2858)/
│   ├── metadata.json
│   ├── cover.jpg
│   ├── ep_001.m3u8
│   └── ...
├── Drama Lain (ID)/
│   └── ...
```

**API akan auto-discover** semua drama di folder `dramas/`
