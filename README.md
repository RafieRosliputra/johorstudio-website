# JohorStudio.com

Website rasmi JohorStudio.com. Website ni statik (HTML, CSS dan JS sahaja), dihidangkan oleh nginx di TrueNAS, dan dibuka ke internet melalui Cloudflare Tunnel. Semua percuma.

```
site/              <- website (inilah yang orang nampak)
  index.html, services.html, portfolio.html, projects.html, about.html, contact.html
  css/style.css    <- warna dan font (tukar di bahagian :root)
  js/main.js
  img/hero/        <- gambar slideshow halaman utama
  img/gallery/     <- gambar portfolio
  data/portfolio.json  <- senarai gambar portfolio (tambah gambar di sini)
  data/videos.json     <- senarai video YouTube
  data/raya.json       <- tarikh butang booking Raya
nginx/default.conf <- tetapan server
docker-compose.yml <- web + Silex + Cloudflare Tunnel
tools/build.py     <- jana semula page HTML (pilihan, untuk tukar teks)
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
```

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
docker run --rm -v "$PWD":/git alpine/git pull
```

Tak perlu restart. nginx terus baca fail baru.

---

## 4. Tambah gambar portfolio sendiri (setiap bulan)

1. Export gambar dalam format WebP:
   - versi besar, sisi panjang 1600px: `nama-gambar.webp`
   - versi kecil, sisi panjang 720px: `nama-gambar-sm.webp`
2. Letak kedua-dua fail dalam `site/img/gallery/`
3. Buka `site/data/portfolio.json` dan tambah satu baris di atas senarai:

```json
{"file": "nama-gambar", "category": "multicam", "caption": "Penerangan ringkas dalam English"},
```

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

## 6. Butang booking Raya

Butang dan jalur "Raya photoshoot" keluar secara automatik antara tarikh `start` (awal Ramadan) dan `end` (2 minggu selepas Raya) dalam `site/data/raya.json`. Tarikh tahun depan adalah anggaran, jadi semak setiap tahun.

---

## Nota

- Gambar budak (tadika) belum dimasukkan. Bila muka dah ditukar guna AI, letak dalam `site/img/gallery/` dan tambah dalam `portfolio.json`.
- Font: Archivo, dari Google Fonts.
- Borang enquiry tak simpan apa-apa. Ia buka WhatsApp dengan maklumat yang client isi.
