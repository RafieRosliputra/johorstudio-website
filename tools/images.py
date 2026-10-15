"""Builds all website images from original files.
gallery: name-sm.webp (720), name.webp (1600), name-full.webp (native, non-BTS only)
hero:    name.webp (2560 landscape), name-m.webp (mobile source, 1440 long edge)
Also computes focal points (where people are) for object-position.
"""
import os, json
from PIL import Image, ImageOps, ImageEnhance

U = '/mnt/user-data/uploads/'
T = U + 'Telegram Desktop/'; P = U + 'PORTFOLIO/'; C = U + 'crew/'; S = U + 'DONE/CAPTIONED ISNIN/'
B = U + 'BTS 20261010 Butterfly 22nd convocation - Trove Hotel/'
A = U + 'allphotos/'
M = U + 'PORTFOLIO/PORT/'
def mcp(p): return M + [f for f in os.listdir(M) if f.startswith(p)][0]

REPO = '/home/claude/johorstudio-website/site/'

# ---------- gallery: (name, source, category, caption) ----------
G = [
 # multicam (BTS)
 ("bts-butterfly-operator-crowd", B+"IMG_20261010_184436.jpg", "multicam", "Camera operator on stage, Butterfly 22nd Convocation, Trove Hotel JB"),
 ("bts-multiview-switcher-01", mcp("101979424"), "multicam", "Multiview switcher during an awards ceremony"),
 ("bts-adtec2026-camera-row", T+"IMG_20260922_101028.jpg", "multicam", "Camera positions, ADTEC JTM 29th Convocation 2026"),
 ("bts-butterfly-two-operators-wide", B+"IMG_20261010_184429.jpg", "multicam", "Two operators covering the stage and audience"),
 ("bts-graduation-hall-camera", mcp("273770379"), "multicam", "Floor camera at a school graduation"),
 ("bts-adtec2026-viewfinder", T+"IMG_9708.JPG", "multicam", "Viewfinder on the stage camera, ADTEC JTM 2026"),
 ("bts-butterfly-gimbal-monitor", B+"IMG_9887.jpeg", "multicam", "Gimbal camera with field monitor"),
 ("bts-butterfly-control-room-mixer", B+"IMG_9879.jpeg", "multicam", "Control room overlooking the ballroom"),
 ("bts-adtec2026-operator", T+"IMG_9719.JPG", "multicam", "Camera operator, ADTEC JTM 29th Convocation"),
 ("bts-team-photo-adtec2026", T+"IMG_9703.JPG", "multicam", "Our crew at ADTEC JTM 29th Convocation 2026"),
 ("bts-ballroom-stage-lighting", mcp("255474255"), "multicam", "Ballroom stage before the event"),
 ("bts-adtec2026-switcher-desk", T+"IMG_9709.JPG", "multicam", "Live switching desk among the audience, ADTEC JTM 2026"),
 ("bts-uthm-hall-camera", T+"IMG_20260922_091605.jpg", "multicam", "Stage camera framing the convocation"),
 # livestream (BTS)
 ("bts-outdoor-control-tent", mcp("258365905"), "livestream", "Outdoor control tent for a live broadcast"),
 ("bts-outdoor-camera-rain", mcp("257460239"), "livestream", "Shooting live in the rain"),
 ("bts-live-talkshow-screen", mcp("133484951"), "livestream", "Live talk show broadcast to Facebook"),
 ("bts-virtual-studio-live", mcp("164826802"), "livestream", "Virtual studio with a live Zoom panel"),
 ("bts-greenscreen-studio-01", mcp("162688085"), "livestream", "Green screen studio set up on site"),
 ("bts-greenscreen-studio-02", mcp("163203726"), "livestream", "Studio set with LED wall and cameras"),
 ("bts-control-room-2022", T+"20220616_142620.jpg", "livestream", "Control room for a hybrid event"),
 ("bts-greenscreen-live-2022", T+"20220616_142829.jpg", "livestream", "Green screen live presentation"),
 ("bts-live-operator-zoom", mcp("245929920"), "livestream", "Operator managing Zoom guests on air"),
 ("bts-kpj-livestream-01", T+"IMG_20260227_152546.jpg", "livestream", "Healthcare talk, live stream set"),
 ("bts-kpj-livestream-02", T+"IMG_20260227_160531.jpg", "livestream", "Healthcare talk, camera and monitor"),
 ("bts-multiview-switcher-02", mcp("118222798"), "livestream", "Multiview monitoring during a live event"),
 ("bts-butterfly-control-desk", B+"IMG_9890.jpeg", "livestream", "Control desk with monitors and audio"),
 ("bts-crew-operator-headset", C+"_R3_0581.webp", "livestream", "Operators on comms during the show"),
 ("bts-crew-wireless-rx", C+"_R3_1521.webp", "livestream", "Wireless video receivers on site"),
 ("bts-talkshow-studio", mcp("133586655"), "livestream", "Talk show set ready for broadcast"),
 # videography (BTS)
 ("bts-interview-setup", T+"IMG_20260603_143440.jpg", "videography", "Interview set-up with key light"),
 ("bts-camera-operator-2022", T+"20220531_091954.jpg", "videography", "Event videography, awards dinner"),
 ("bts-butterfly-shoulder-rig", B+"IMG_9882.jpeg", "videography", "Shoulder rig coverage, ballroom floor"),
 ("bts-butterfly-riser-camera", B+"IMG_9902.jpeg", "videography", "Long-lens camera on the riser"),
 ("bts-crew-camera-gimbal", C+"_R3_0453.webp", "videography", "Gimbal operator at the photobooth"),
 ("bts-crew-camera-stand", C+"_R3_1137.webp", "videography", "Camera crew in the ballroom"),
 ("bts-crew-camera-ops", C+"_R3_1523.webp", "videography", "Camera on a covered stand"),
 ("bts-crew-ballroom", C+"_R3_1388.webp", "videography", "Our videographer on the ballroom floor"),
 ("bts-factory-shoot", mcp("141723470"), "videography", "Corporate video shoot in a testing lab"),
 # photography (full res)
 ("photo-event-award-ceremony", T+"C DSC03706 151.jpg", "photography", "Award ceremony, state-level honours"),
 ("photo-event-award-ceremony-02", T+"DSC03840 238.jpg", "photography", "Award ceremony, state-level honours"),
 ("photo-event-symposium-speaker", T+"20220618_083746.jpg", "photography", "Primary Care Symposium, DoubleTree JB"),
 ("photo-event-symposium-hall", T+"20220618_083731.jpg", "photography", "Symposium hall, DoubleTree JB"),
 ("photo-event-speaker-perisind", mcp("166827472"), "photography", "Keynote speaker at a corporate launch"),
 ("photo-event-mock-cheque", mcp("167274279"), "photography", "Sponsorship presentation"),
 ("photo-corporate-portrait-01", T+"DSC05166.jpg", "photography", "Corporate portrait"),
 ("photo-corporate-portrait-06", T+"DSC05165.jpg", "photography", "Corporate portrait, full length"),
 ("photo-corporate-portrait-07", T+"DSC05155.jpg", "photography", "Portrait in team uniform"),
 ("photo-corporate-portrait-02", mcp("141880658"), "photography", "Corporate portrait"),
 ("photo-corporate-portrait-03", mcp("134705459"), "photography", "Executive portrait"),
 ("photo-corporate-portrait-04", mcp("87710453"), "photography", "Official portrait, police officer"),
 ("photo-corporate-portrait-05", T+"DSC05178.jpg", "photography", "Official portrait in baju Melayu"),
 ("photo-corporate-portrait-08", mcp("135595082"), "photography", "Portrait in baju Melayu, low key"),
 ("photo-corporate-portrait-09", mcp("141946811"), "photography", "Portrait on white"),
 ("photo-corporate-portrait-10", P+"20190109_2_0074.jpg", "photography", "Executive portrait, painted backdrop"),
 ("photo-sports-motocross-01", T+"DSC07449.jpg", "photography", "Motocross, mid-air"),
 ("photo-sports-motocross-03", T+"DSC07495.jpg", "photography", "Motocross, berm turn"),
 ("photo-sports-motocross-02", T+"DSC07431.jpg", "photography", "Motocross rider portrait"),
 ("photo-landscape-pier", P+"f50092192.jpg", "photography", "Sunset at the pier, Johor"),
 ("photo-landscape-waterfall", P+"f80396216.jpg", "photography", "Waterfall, long exposure"),
 ("photo-city-light-trails", P+"DSC03897.jpg", "photography", "City light trails at dusk"),
 # studio / fashion / product (full res)
 ("studio-fashion-01", T+"_R3_1032.jpg", "studio", "Fashion shoot, hijab collection"),
 ("studio-fashion-09", T+"_R3_1033.jpg", "studio", "Fashion shoot, window light"),
 ("studio-fashion-02", T+"_R3_1117.jpg", "studio", "Fashion shoot, interior styling"),
 ("studio-fashion-10", T+"_R3_1371.jpg", "studio", "Fashion shoot, satin scarf"),
 ("studio-fashion-03", T+"_R3_1484.jpg", "studio", "Fashion shoot, pink scarf"),
 ("studio-fashion-11", T+"_R3_1591.jpg", "studio", "Fashion shoot, corporate look"),
 ("studio-fashion-12", T+"_R3_1746.jpg", "studio", "Fashion shoot, rooftop garden"),
 ("studio-fashion-05", T+"_R3_1776.jpg", "studio", "Fashion shoot, garden"),
 ("studio-fashion-04", T+"_R3_1956.jpg", "studio", "Fashion shoot, poolside"),
 ("studio-fashion-13", T+"_R3_1981.jpg", "studio", "Fashion shoot, golden hour"),
 ("studio-fashion-06", P+"20181106_W_0113.jpg", "studio", "Studio fashion, satin"),
 ("studio-fashion-07", P+"DSC00244.jpg", "studio", "Fashion shoot, Japanese garden"),
 ("studio-fashion-14", P+"20180924_W_0432.jpg", "studio", "Bridal collection, studio"),
 ("studio-fashion-15", P+"DSC01812.jpg", "studio", "Studio fashion, pink backdrop"),
 ("studio-fashion-16", P+"DSC00341.jpg", "studio", "Studio portrait, window light"),
 ("studio-fashion-17", P+"20190124_2_0194.jpg", "studio", "Studio fashion, green backdrop"),
 ("studio-fashion-18", P+"DSC08456.jpg", "studio", "Studio fashion, low key"),
 ("studio-fashion-19", P+"DSC07969.jpg", "studio", "Night fashion, bokeh"),
 ("studio-fashion-20", P+"DSC02615.jpg", "studio", "Lifestyle, handbag collection"),
 ("studio-fashion-21", P+"DSC08111.jpg", "studio", "Outdoor fashion, mosque architecture"),
 ("studio-fashion-08", T+"wt DSC04972.jpg", "studio", "Lifestyle fashion shoot"),
 ("studio-fashion-22", T+"wt DSC05105.jpg", "studio", "Lifestyle fashion, two models"),
 ("studio-beauty-01", P+"20180830 - 0031.jpg", "studio", "Beauty close-up"),
 ("studio-beauty-02", P+"aDSC02448.jpg", "studio", "Black and white portrait"),
 ("studio-corporate-01", P+"_R3_0177.webp", "studio", "Corporate studio portrait"),
 ("studio-outdoor-portrait-01", T+"DSC00118 (2).jpg", "studio", "Outdoor portrait"),
 ("studio-product-01", P+"20180926_2_0028.jpg", "studio", "Product, leather wallet"),
 ("studio-product-04", P+"20181012_2_0144.jpg", "studio", "Product with model, beauty drink"),
 ("studio-product-02", T+"20170320 - 0030.jpg", "studio", "Product, lip gloss"),
 ("studio-product-05", T+"20170320 - 0023.jpg", "studio", "Product, lip gloss range"),
 ("studio-product-03", P+"DSC02696.jpg", "studio", "Product, food"),
 ("studio-product-06", P+"20160606 - 0060.jpg", "studio", "Product, food styling"),
 # convocation & school (full res)
 ("convo-graduation-stage-01", T+"DSC08461.JPG", "convocation", "Convocation, on-stage scroll presentation"),
 ("convo-graduation-stage-02", T+"DSC08494.JPG", "convocation", "Convocation, on-stage scroll presentation"),
 ("school-class-photo-01", S+"5C - 01.jpg", "convocation", "Class photo, SMK Kulai Besar 2026"),
 ("school-class-photo-02", S+"TVPSS - 01.jpg", "convocation", "Group photo, SMK Kulai Besar 2026"),
 ("school-class-photo-03", S+"BadanPengawas - 01.jpg", "convocation", "Prefects board, SMK Kulai Besar 2026"),
 ("school-class-photo-04", S+"3B - 01.jpg", "convocation", "Class photo, SMK Kulai Besar 2026"),
]

# ---------- hero: (name, landscape source, mobile source or None, caption) ----------
H = [
 ("hero-01", B+"IMG_20261010_184436.jpg", None, "Live camera on stage, Butterfly 22nd Convocation, Trove Hotel"),
 ("hero-02", P+"20181106_W_0113.jpg", T+"_R3_1032.jpg", "Studio fashion photography"),
 ("hero-03", T+"IMG_9709.JPG", T+"IMG_9719.JPG", "Live switching, ADTEC JTM 29th Convocation 2026"),
 ("hero-04", T+"DSC07495.jpg", T+"DSC07449.jpg", "Motorsport photography"),
 ("hero-05", C+"_R3_1388.webp", C+"_R3_1138.webp", "Our crew on the ballroom floor"),
 ("hero-06", T+"_R3_1033.jpg", T+"_R3_1746.jpg", "Fashion and lifestyle shoots"),
 ("hero-07", T+"IMG_20260922_091605.jpg", None, "Multicam coverage, ADTEC JTM 2026"),
 ("hero-08", T+"C DSC03706 151.jpg", T+"DSC05166.jpg", "Award ceremonies and official portraits"),
]

FOCAL = {  # (desktop x%,y%), (mobile x%,y%) — where the people are
 "hero-01": ((72, 40), (82, 40)), "hero-02": ((45, 35), (55, 30)),
 "hero-03": ((40, 50), (55, 45)), "hero-04": ((45, 50), (50, 35)),
 "hero-05": ((58, 45), (55, 40)), "hero-06": ((55, 35), (50, 35)),
 "hero-07": ((50, 55), (40, 55)), "hero-08": ((50, 8), (50, 30)),
}

def load(src):
    return ImageOps.exif_transpose(Image.open(src)).convert('RGB')

def save(im, path, maxside, q):
    im = im.copy()
    if maxside and max(im.size) > maxside:
        im.thumbnail((maxside, maxside), Image.LANCZOS)
    im.save(path, 'WEBP', quality=q, method=6)

def is_phone_bts(name):
    return name.startswith('bts-')

if __name__ == '__main__':
    gdir = REPO + 'img/gallery/'; hdir = REPO + 'img/hero/'
    for d in (gdir, hdir):
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d): os.remove(d + f)
    items = []
    for name, src, cat, cap in G:
        im = load(src)
        if is_phone_bts(name):
            im = ImageOps.autocontrast(im, cutoff=0.4); im = ImageEnhance.Color(im).enhance(1.05)
        save(im, gdir + name + '-sm.webp', 720, 74)
        save(im, gdir + name + '.webp', 1600, 78)
        it = {"file": name, "category": cat, "caption": cap}
        if not is_phone_bts(name):
            save(im, gdir + name + '-full.webp', 6000, 82)
            it["full"] = True
            it["size"] = f"{im.size[0]}×{im.size[1]}"
        items.append(it)
        print(name, im.size)
    hero = []
    for name, src, msrc, cap in H:
        im = load(src)
        if 'IMG_' in src or src.startswith(B):
            im = ImageOps.autocontrast(im, cutoff=0.4)
        (fx, fy), (mfx, mfy) = FOCAL[name]
        save(im, hdir + name + '.webp', 2560, 72)
        save(im, hdir + name + '-thumb.webp', 480, 70)
        m = load(msrc) if msrc else im
        if msrc and ('IMG_' in msrc):
            m = ImageOps.autocontrast(m, cutoff=0.4)
        save(m, hdir + name + '-m.webp', 1600, 72)
        hero.append({"name": name, "caption": cap, "pos": f"{fx}% {fy}%", "mpos": f"{mfx}% {mfy}%"})
        print(name, (fx, fy), (mfx, mfy))
    json.dump(hero, open('/home/claude/hero.json', 'w'), indent=1)
    data = {"_help": "Tambah gambar: letak name-sm.webp (720px), name.webp (1600px) dan name-full.webp (resolusi asal) dalam img/gallery, kemudian tambah satu baris di sini. 'full': true bila ada versi -full. category: multicam, livestream, videography, photography, studio, convocation",
            "items": items}
    json.dump(data, open(REPO + 'data/portfolio.json', 'w'), indent=1, ensure_ascii=False)
