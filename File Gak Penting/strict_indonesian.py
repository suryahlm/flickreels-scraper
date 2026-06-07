#!/usr/bin/env python3
"""Get STRICTLY Indonesian dramas only - by manual curation."""
import boto3
from botocore.config import Config
import re

s3 = boto3.client('s3',
    endpoint_url='https://caa84fe6b1be065cda3836f0dac4b509.r2.cloudflarestorage.com',
    aws_access_key_id='a4903ea93c248388b6e295d6cdbc8617',
    aws_secret_access_key='5768603adc5e7902f35f74137771cee70510425acf39a66701d4ecc3f626dbe9',
    config=Config(signature_version='s3v4')
)

bucket = 'asiandrama-cdn'

# STRICTLY Indonesian titles (manually curated) - judulnya bahasa Indonesia
INDONESIAN_TITLES = [
    # Confirmed Indonesian titles
    ('894', 'Adik lpar Memanjakanku（Dubbing）'),
    ('4840', 'Aduh! Dukun Cilik Cari Cuan'),
    ('5190', 'Aku Ditakdirkan Milikmu'),
    ('5136', 'Anak Imut Turun dari Langit'),
    ('4058', 'Anak Lucu Hoki Datang'),
    ('3108', 'Ayah Pacarku, Suamiku'),
    ('5119', 'Azab dari Dewi Pena'),
    ('2655', 'Bayang-Bayang Kehidupan'),
    ('3694', 'Bukan Bidakmu'),
    ('721', 'Cinta Di Ujung Senja'),
    ('978', 'Cinta Di Ujung Senja（Dubbing）'),
    ('5194', 'Cinta Diam Jadi Nyata'),
    ('5122', 'Cinta Tanpa Keraguan'),
    ('487', 'Cintaku Hadir Di Kehidupan Selanjutnya'),
    ('2491', 'Dimanja Tiga Menantu Setelah Cerai'),
    ('2343', 'Dokter Jenius Terlahir Kembali'),
    ('5071', 'Godaan Sengaja'),
    ('4009', 'Godaan di Malam Hari'),
    ('3495', 'Hari Tunangan Anakku, Kubatalkan'),
    ('4255', 'Hidup Lagi, Kubalas dendam'),
    ('5137', 'Istri Gemuk Dimanjakan'),
    ('495', 'Istri Kesayangan Mafia'),
    ('977', 'Istri Kesayangan Mafia（Dubbing）'),
    ('5235', 'Jangan Ganggu Nenek'),
    ('5202', 'Kebenaran Tak Terkubur'),
    ('963', 'Kejayaanku Setelah Berpisah'),
    ('5089', 'Kok Nyonya Gitu Kejam_'),
    ('4440', 'Legenda Keluarga Japhar'),
    ('3658', 'Leluhur 10 Tahun​​'),
    ('5159', 'Maaf, Anak Ini Bukan Milikmu'),
    ('3985', 'Makin Ditahan, Makin Penasaran'),
    ('4464', 'Masa Bersinarku'),
    ('4784', 'Menaklukkan Suami Nakal'),
    ('533', 'Menikah lagi dengan Ketua Direksi(Dubbing)'),
    ('5135', 'Naga Emas Lahir, Takdir Berbalik'),
    ('2186', 'Nenek Muda_ Kebangkitan Keluarga 2'),
    ('3674', 'Nenek Muda_ Kebangkitan Keluarga 3'),
    ('4187', 'Nyonya Muda Si Mulut Sial'),
    ('4158', 'Nyonya Muda Tak Terkalahkan 2'),
    ('2518', 'Nyonya Muda yang Tidak Terkalahkan'),
    ('5220', 'Pacarku Ternyata Dewi Kampus'),
    ('5031', 'Pangeran Merah Muda'),
    ('5247', 'Peramal Wanita'),
    ('5099', 'Romansa Om'),
    ('4511', 'Romansa di Rumah Mewah'),
    ('4839', 'Salah Goda'),
    ('5043', 'Sang Putri Dilindungi Ibu'),
    ('3164', 'Sayang, Aku Benaran Amnesia'),
    ('5226', 'Suami Miskin Jadi Bos'),
    ('2691', 'Surga di Telapak Kaki Ibu'),
    ('2858', 'Tak Bisa Melepasmu'),
    ('1445', 'Takdir Cinta dengan Kaisar(Dubbing)'),
]

print(f"STRICTLY INDONESIAN DRAMAS: {len(INDONESIAN_TITLES)}")
print()
for id, title in sorted(INDONESIAN_TITLES, key=lambda x: x[1]):
    print(f"  {id}: {title}")

# Output TypeScript set
print("\n\n// TypeScript Set for STRICTLY INDONESIAN drama IDs:")
print("const INDONESIAN_DRAMA_IDS = new Set([")
ids = [id for id, _ in INDONESIAN_TITLES]
chunks = [ids[i:i+12] for i in range(0, len(ids), 12)]
for chunk in chunks:
    formatted = ', '.join([f"'{id}'" for id in chunk])
    print(f"    {formatted},")
print("]);")
