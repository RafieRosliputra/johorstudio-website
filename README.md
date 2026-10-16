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

## 1. Di mana semuanya berada

Website berjalan sebagai app `johorstudio` di TrueNAS (**Apps > Installed**). Semua fail ada dalam dataset `/mnt/ssd/website`:

```
/mnt/ssd/website/repo      <- repo ni (git clone)
/mnt/ssd/website/uploads   <- folder projek kau (share SMB: smb://192.168.0.100/website-uploads)
/mnt/ssd/website/silex     <- data Silex
```

| Alamat | Apa | Siapa boleh buka |
|---|---|---|
| https://johorstudio.com | Website | Semua orang |
| https://webmaster.johorstudio.com | Panel webmaster: butang Publish dan Update | Email kau sahaja (Cloudflare Access) |
| https://editor.johorstudio.com | Silex, untuk bina page baru | Email kau sahaja (Cloudflare Access) |

Dalam rumah, alamat yang sama ada di `http://192.168.0.100:8080` (website), `:8090` (webmaster) dan `:6805` (Silex).

Domain disambung melalui tunnel Cloudflare `m10` yang sedia ada (Zero Trust > Networks > Tunnels). Page yang dibina dalam Silex dan di-publish keluar di `johorstudio.com/pages/`.

---

## 2. Pasang semula atau baiki

Login ke TrueNAS (`ssh root@192.168.0.100`) dan jalankan:

```sh
curl -fsSL https://raw.githubusercontent.com/RafieRosliputra/johorstudio-website/main/deploy/setup-truenas.sh -o /tmp/js.sh && bash /tmp/js.sh
```

Skrip ni selamat dijalankan berulang kali. Ia buat dataset, share SMB, tarik fail dari GitHub, bina image tools, jana page dan pasang atau kemas kini app `johorstudio`.

---

## 3. Update website (bila Claude dah push perubahan)

Buka https://webmaster.johorstudio.com dan tekan **Update from GitHub and publish**. Kalau tukar sesuatu dalam folder `tools/` (contohnya Dockerfile), jalankan skrip di bahagian 2.

---

## Projects: tambah posting sendiri (macam blog)

Setiap folder = satu posting dalam page Projects. Kau boleh buat banyak folder sekali gus, kemudian jalankan satu arahan.

### a) Buka folder upload

Dari Mac: Finder > Go > Connect to Server > `smb://192.168.0.100/website-uploads`, login dengan user TrueNAS kau (bukan root).

### b) Buat satu folder untuk setiap projek

Nama folder: **tarikh dan tajuk**. Tarikh dan tajuk diambil dari nama folder kalau `project.md` tak tulis.

```
website-uploads/
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

Buka https://webmaster.johorstudio.com dan tekan **Publish projects**. Panel tu juga senaraikan folder yang ada dan tunjuk log semasa publish berjalan.

Semua folder dalam `website-uploads` jadi posting baru, disusun ikut tarikh (terbaru dulu). Posting terbaru juga keluar di halaman utama bahagian "Recent projects". Untuk edit posting, ubah folder atau `project.md`, kemudian tekan **Publish projects** sekali lagi. Untuk buang posting, padam foldernya dan tekan **Publish projects**.

Gambar yang terbuka bila diklik (1600px dan resolusi penuh) diletakkan logo JohorStudio.com di bucu kanan bawah secara automatik. Gambar kecil (thumbnail) tak ada watermark. Gambar asal dalam folder kau tak diubah.

Folder dalam `projects/` (dalam repo) ialah projek yang Claude letak. Kalau kau buat folder dengan nama sama dalam `website-uploads`, folder kau yang dipakai.

Nota: preview di GitHub Pages hanya nampak folder dalam `projects/` repo. Folder dalam TrueNAS hanya keluar di johorstudio.com.

---

## 4. Tambah gambar portfolio sendiri (setiap bulan)

1. Export gambar dalam format WebP (kualiti lebih kurang 80):
   - versi kecil, sisi panjang 720px: `nama-gambar-sm.webp`
   - versi biasa, sisi panjang 1600px: `nama-gambar.webp`
   - versi penuh, resolusi asal: `nama-gambar-full.webp` (tak perlu untuk gambar BTS)
2. Letak `nama-gambar-sm.webp` dalam `site/img/gallery/`, dan `nama-gambar.webp` serta `nama-gambar-full.webp` dalam `media/gallery/` (watermark diletak automatik bila kau tekan **Publish projects**)
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

Silex untuk kau bina **page baru** (contohnya landing page promosi Raya) secara drag and drop. Buka https://editor.johorstudio.com (atau butang **Open Silex editor** di panel webmaster). Bila page siap, guna **Publish**. Page tu keluar di `johorstudio.com/pages/`.

Page utama website ni ditulis dalam HTML biasa, bukan dalam Silex. Untuk tukar teks page utama, minta Claude, atau edit `tools/build.py` dan jalankan `python3 tools/build.py`.

---

## 6. Raya dan butang WhatsApp

- Hanya page `raya.html` ada butang "Book a Raya slot", yang pergi ke https://bookings.johorstudio.cc/public. Link ni ditukar di `RAYA_URL` dalam `tools/layout.py`.
- Jalur "Raya photoshoot" di atas setiap page, dan butang Raya di halaman utama, pergi ke page `raya.html`. Ia keluar secara automatik antara tarikh `start` (awal Ramadan) dan `end` (2 minggu selepas Raya) dalam `site/data/raya.json`. Tarikh tahun depan adalah anggaran, jadi semak setiap tahun.
- Page lain guna borang enquiry (`contact.html`) atau WhatsApp. Butang WhatsApp buka chat dengan mesej "Hi Rafi" (tukar di `WA` dalam `tools/layout.py`). Borang enquiry pula hantar butiran yang client isi.

---

## Watermark gambar portfolio dan Raya

Gambar asal (tanpa logo) disimpan dalam `media/gallery/` dan `media/raya/`: versi 1600px `nama.webp` dan versi penuh `nama-full.webp`. Thumbnail `nama-sm.webp` kekal dalam `site/img/`. Bila kau tekan **Publish projects** atau **Update**, salinan berwatermark dibuat dalam `site/img/` secara automatik. Jangan letak gambar terus dalam `site/img/gallery/` kecuali thumbnail.

Saiz dan kelutsinaran logo boleh diubah di `WIDTH` dan `OPACITY` dalam `tools/watermark.py`. Lepas ubah, tekan **Publish projects** dan semua gambar dibuat semula dari gambar asal. Notis hak cipta yang keluar bila gambar dibuka penuh ditulis dalam `LEGAL` di `tools/layout.py`.

## Nota

- Gambar budak (tadika) belum dimasukkan. Bila muka dah ditukar guna AI, letak macam langkah di bahagian 4 dan tambah dalam `portfolio.json`.
- Font: Archivo, dari Google Fonts.
- Borang enquiry tak simpan apa-apa. Ia buka WhatsApp dengan maklumat yang client isi.

## Slideshow halaman utama

Gambar ada dalam `site/img/hero/`: `hero-01.webp` untuk laptop dan `hero-01-m.webp` untuk phone (boleh guna gambar portrait). Titik fokus, iaitu di mana orang berada dalam gambar, ditetapkan dalam `HERO` di `tools/build.py` (`pos` untuk laptop, `mpos` untuk phone, dalam peratus x dan y).
