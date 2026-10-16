# JohorStudio.com

Website rasmi JohorStudio.com. Website ni statik (HTML, CSS dan JS sahaja), dihidangkan oleh nginx di TrueNAS, dan dibuka ke internet melalui Cloudflare Tunnel. Semua percuma.

```
site/              <- website (inilah yang orang nampak)
  index.html, services.html, portfolio.html, raya.html, about.html, contact.html
  projects/        <- DIJANA oleh tools/projects.py (jangan edit, tak disimpan dalam git)
  css/style.css    <- warna dan font (tukar di bahagian :root)
  js/main.js
  img/hero/        <- gambar slideshow halaman utama
  img/gallery/     <- gambar portfolio
  img/raya/        <- gambar page Raya (senarai dalam data/raya-gallery.json)
  data/portfolio.json  <- senarai gambar portfolio (tambah gambar di sini)
  data/videos.json     <- senarai video YouTube
  data/raya.json       <- tarikh jalur dan butang Raya
nginx/default.conf <- tetapan server
docker-compose.yml <- web + Silex + Cloudflare Tunnel
tools/build.py     <- jana semula page HTML (pilihan, untuk tukar teks)
tools/projects.py  <- tukar folder projek jadi posting Projects
projects/          <- folder projek yang Claude letak (setiap folder = satu posting)
publish.sh         <- jalankan bila kau tambah folder projek baru
update.sh          <- tarik update dari GitHub + publish sekali gus
```

---

## 1. Kali pertama: pasang di TrueNAS

Langkah ni guna Shell TrueNAS. Kau boleh guna **System > Shell** dalam UI TrueNAS, atau `ssh` dari Mac.

### a) Clone repo

```sh
ssh admin@IP-TRUENAS
sudo -i
cd /mnt/ssd
docker run --rm -v /mnt/ssd:/git alpine/git clone https://github.com/RafieRosliputra/johorstudio-website.git
cd johorstudio-website
```

Kita guna `alpine/git` dalam Docker sebab TrueNAS tak semestinya ada `git`.

### b) Sediakan .env

```sh
cp .env.example .env
sed -i "s|^SILEX_SESSION_SECRET=.*|SILEX_SESSION_SECRET=$(openssl rand -base64 32)|" .env
```

### c) Hidupkan website

```sh
docker compose up -d web
./publish.sh
```

`./publish.sh` jana page Projects. Kali pertama ambil masa beberapa minit sebab semua gambar ditukar ke WebP. Lepas tu, hanya gambar baru diproses.

Buka `http://IP-TRUENAS:8080` dari laptop. Website patut keluar.

---

## 2. Sambung ke johorstudio.com (Cloudflare Tunnel, percuma)

1. Log masuk Cloudflare, pergi **Zero Trust > Networks > Tunnels > Create a tunnel**
2. Pilih **Cloudflared**, beri nama `johorstudio`
3. Bila keluar arahan install, salin **token** sahaja (rentetan panjang selepas `--token`)
4. Letak dalam `.env`: `TUNNEL_TOKEN=token-tadi`
5. Di Cloudflare, bahagian **Public Hostname**:
   - Subdomain: kosong, Domain: `johorstudio.com`, Service: `HTTP` > `web:80`
   - Tambah satu lagi untuk `www`, dengan service yang sama
6. Hidupkan tunnel:

```sh
docker compose --profile tunnel up -d
```

Buka https://johorstudio.com.

---

## 3. Update website (bila Claude dah push perubahan)

```sh
ssh admin@IP-TRUENAS
sudo -i
cd /mnt/ssd/johorstudio-website
./update.sh
```

`update.sh` tarik perubahan dari GitHub, kemudian jana semula page Projects. Tak perlu restart. nginx terus baca fail baru.

---

## Projects: tambah posting sendiri (macam blog)

Setiap folder = satu posting dalam page Projects. Kau boleh buat banyak folder sekali gus, kemudian jalankan satu arahan.

### a) Sediakan folder upload (sekali sahaja)

1. Dalam TrueNAS, buat dataset, contoh `/mnt/ssd/website-projects`
2. Kongsi dataset tu melalui SMB (**Shares > Windows (SMB) Shares > Add**), supaya boleh buka dari Mac (Finder > Go > Connect to Server > `smb://IP-TRUENAS`)
3. Dalam `.env`, pastikan `UPLOADS_DIR=/mnt/ssd/website-projects`

### b) Buat satu folder untuk setiap projek

Nama folder: **tarikh dan tajuk**. Tarikh dan tajuk diambil dari nama folder kalau `project.md` tak tulis.

```
website-projects/
  20261103 Majlis Konvokesyen ABC/
    project.md
    IMG_0001.jpg
    IMG_0002.jpg
    bts-kamera-01.jpg       <- nama bermula "bts" = gambar BTS, tiada versi resolusi penuh
  20261115-16 Karnival Sukan XYZ/   <- acara 2 hari (15 hingga 16)
    project.md
    ...
```

- Gambar: JPG, PNG, WebP atau HEIC. Saiz asal pun boleh, skrip akan kecilkan dan tukar ke WebP.
- Gambar keluar ikut susunan nama fail. Letak sekurang-kurangnya 10 gambar.
- Folder yang namanya bermula dengan `_` dianggap draf dan tak dipaparkan.
- Jangan masukkan gambar yang menampakkan muka budak dengan jelas, kecuali muka dah ditukar.

### c) Isi `project.md`

Salin contoh ni (ada juga dalam `tools/project-template.md`). Tulis dalam English.

```
---
title: Majlis Konvokesyen ABC 2026
date: 2026-11-03
location: Dewan Besar, Kulai, Johor
client: Kolej ABC
services: Multicam, livestream, photography
cover: IMG_0005.jpg
---
Tulis penerangan program di sini. Perenggan kosong = perenggan baru.

**Teks tebal**, *teks condong*, dan senarai:
- Item satu
- Item dua
```

Semua baris dalam bahagian `---` adalah pilihan. `cover` ialah gambar untuk kad projek (kalau tiada, gambar pertama). Tambah `end: 2026-11-04` untuk acara lebih dari sehari, atau `hidden: yes` untuk sorok posting.

### d) Publish

```sh
ssh admin@IP-TRUENAS
sudo -i
cd /mnt/ssd/johorstudio-website
./publish.sh
```

Semua folder dalam `website-projects` jadi posting baru, disusun ikut tarikh (terbaru dulu). Posting terbaru juga keluar di halaman utama bahagian "Recent projects". Untuk edit posting, ubah folder atau `project.md`, kemudian jalankan `./publish.sh` sekali lagi. Untuk buang posting, padam foldernya dan jalankan `./publish.sh`.

Gambar yang terbuka bila diklik (1600px dan resolusi penuh) diletakkan logo JohorStudio.com di bucu kanan bawah secara automatik. Gambar kecil (thumbnail) tak ada watermark. Gambar asal dalam folder kau tak diubah.

Folder dalam `projects/` (dalam repo) ialah projek yang Claude letak. Kalau kau buat folder dengan nama sama dalam `website-projects`, folder kau yang dipakai.

Nota: preview di GitHub Pages hanya nampak folder dalam `projects/` repo. Folder dalam TrueNAS hanya keluar di johorstudio.com.

---

## 4. Tambah gambar portfolio sendiri (setiap bulan)

1. Export gambar dalam format WebP (kualiti lebih kurang 80):
   - versi kecil, sisi panjang 720px: `nama-gambar-sm.webp`
   - versi biasa, sisi panjang 1600px: `nama-gambar.webp`
   - versi penuh, resolusi asal: `nama-gambar-full.webp` (tak perlu untuk gambar BTS)
2. Letak `nama-gambar-sm.webp` dalam `site/img/gallery/`, dan `nama-gambar.webp` serta `nama-gambar-full.webp` dalam `media/gallery/` (watermark diletak automatik bila `./publish.sh` dijalankan)
3. Buka `site/data/portfolio.json` dan tambah satu baris di atas senarai:

```json
{"file": "nama-gambar", "category": "studio", "caption": "Penerangan ringkas dalam English", "full": true, "size": "6000×4000"},
```

Untuk gambar BTS, buang `"full"` dan `"size"`, supaya bila diklik ia cuma buka versi 1600px.

`category` mesti salah satu dari: `multicam`, `livestream`, `videography`, `photography`, `convocation`, `studio`.

Untuk video YouTube, tambah dalam `site/data/videos.json`:

```json
"items": [ {"id": "dQw4w9WgXcQ", "title": "CONSAL XIX livestream"} ]
```

`id` ialah huruf selepas `watch?v=` dalam link YouTube.

---

## 5. Silex (editor visual)

Silex dipasang untuk kau bina **page baru** (contohnya landing page promosi Raya) secara drag and drop. Ia hanya untuk rangkaian rumah (LAN), dan tak dibuka ke internet.

```sh
docker compose --profile editor up -d
```

Buka `http://IP-TRUENAS:6805`. Bila page siap, guna **Publish**. Hasilnya keluar dalam `silex-data/hosting/`. Salin fail HTML tu ke `site/` untuk jadikan sebahagian website.

Page utama website ni ditulis dalam HTML biasa, bukan dalam Silex. Untuk tukar teks page utama, minta Claude, atau edit `tools/build.py` dan jalankan `python3 tools/build.py`.

---

## 6. Raya dan butang WhatsApp

- Hanya page `raya.html` ada butang "Book a Raya slot", yang pergi ke https://bookings.johorstudio.cc/public. Link ni ditukar di `RAYA_URL` dalam `tools/layout.py`.
- Jalur "Raya photoshoot" di atas setiap page, dan butang Raya di halaman utama, pergi ke page `raya.html`. Ia keluar secara automatik antara tarikh `start` (awal Ramadan) dan `end` (2 minggu selepas Raya) dalam `site/data/raya.json`. Tarikh tahun depan adalah anggaran, jadi semak setiap tahun.
- Page lain guna borang enquiry (`contact.html`) atau WhatsApp. Butang WhatsApp buka chat dengan mesej "Hi Rafi" (tukar di `WA` dalam `tools/layout.py`). Borang enquiry pula hantar butiran yang client isi.

---

## Watermark gambar portfolio dan Raya

Gambar asal (tanpa logo) disimpan dalam `media/gallery/` dan `media/raya/`: versi 1600px `nama.webp` dan versi penuh `nama-full.webp`. Thumbnail `nama-sm.webp` kekal dalam `site/img/`. Bila `./publish.sh` atau `./update.sh` dijalankan, salinan berwatermark dibuat dalam `site/img/` secara automatik. Jangan letak gambar terus dalam `site/img/gallery/` kecuali thumbnail.

Saiz dan kelutsinaran logo boleh diubah di `WIDTH` dan `OPACITY` dalam `tools/watermark.py`. Lepas ubah, jalankan `./publish.sh` dan semua gambar dibuat semula dari gambar asal. Notis hak cipta yang keluar bila gambar dibuka penuh ditulis dalam `LEGAL` di `tools/layout.py`.

## Nota

- Gambar budak (tadika) belum dimasukkan. Bila muka dah ditukar guna AI, letak macam langkah di bahagian 4 dan tambah dalam `portfolio.json`.
- Font: Archivo, dari Google Fonts.
- Borang enquiry tak simpan apa-apa. Ia buka WhatsApp dengan maklumat yang client isi.

## Slideshow halaman utama

Gambar ada dalam `site/img/hero/`: `hero-01.webp` untuk laptop dan `hero-01-m.webp` untuk phone (boleh guna gambar portrait). Titik fokus, iaitu di mana orang berada dalam gambar, ditetapkan dalam `HERO` di `tools/build.py` (`pos` untuk laptop, `mpos` untuk phone, dalam peratus x dan y).
