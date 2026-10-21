#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Вставляет ВАШИ фотографии в сайт студии и собирает один самодостаточный
index.html, который открывается на компьютере, телефоне и планшете
(фото вшиты внутрь файла, отдельная папка с картинками не нужна).

КАК ЗАПУСТИТЬ
-------------
1. Положите свои фото в отдельную папку (например C:\\Users\\User\\Desktop\\фото-студии).
2. Переименуйте их так, как в списке ниже (расширение .jpg / .jpeg / .png / .webp — любое).
3. Запустите:
       python вставить-свои-фото.py "C:\\Users\\User\\Desktop\\фото-студии"
4. Рядом с папкой появится готовый файл  index.html  — его можно открыть,
   отправить в мессенджере, загрузить на хостинг.

Если Pillow не установлен, выполните:  pip install pillow

ИМЕНА ФАЙЛОВ (что куда вставляется)
----------------------------------
    hero.jpg              — большой фон на главном экране
    about.jpg             — портрет мастера (раздел «Обо мне»)
    service-nails.jpg     — маникюр (лиловый гель-лак)
    service-brows.jpg     — оформление бровей
    service-lashes.jpg    — наращивание ресниц
    gallery-1.jpg         — французский
    gallery-2.jpg         — молочный
    gallery-3.jpg         — лиловый
    gallery-4.jpg         — нюдовый
    gallery-5.jpg         — мятный
    gallery-6.jpg         — лавандовый
    gallery-7.jpg         — коралловый
    gallery-8.jpg         — оливковый
    process.jpg           — процесс работы мастера (широкая полоса)

Необязательные файлы можно не класть — тогда останется демо-фото.
"""

import base64
import os
import re
import shutil
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Нужен Pillow. Установите:  pip install pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "site", "index.html")          # шаблон с обычными ссылками на фото
DEFAULT_IMAGES = os.path.join(HERE, "site", "images")          # демо-фото (запасной вариант)

# роль -> (размер по ширине, высота, нужное соотношение сторон)
ROLES = {
    "hero":              (1600, 900, 16 / 9),
    "about":             (900, 1200, 4 / 5),
    "service-nails":     (900, 600, 3 / 2),
    "service-brows":     (900, 600, 3 / 2),
    "service-lashes":    (900, 600, 3 / 2),
    "gallery-1":         (800, 800, 1 / 1),
    "gallery-2":         (800, 800, 1 / 1),
    "gallery-3":         (800, 800, 1 / 1),
    "gallery-4":         (800, 800, 1 / 1),
    "gallery-5":         (800, 800, 1 / 1),
    "gallery-6":         (800, 800, 1 / 1),
    "gallery-7":         (800, 800, 1 / 1),
    "gallery-8":         (800, 800, 1 / 1),
    "process":           (1680, 720, 21 / 9),
}
EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".heif")


def find_photo(folder, role):
    for ext in EXT:
        p = os.path.join(folder, role + ext)
        if os.path.isfile(p):
            return p
    # файлы вида about (1).jpg / about_final.png
    low = role.lower()
    for f in sorted(os.listdir(folder)):
        stem, e = os.path.splitext(f)
        if e.lower() in EXT and low in stem.lower() and stem.lower() != role:
            return os.path.join(folder, f)
    return None


def to_webp(src, dst, w, h, ratio):
    im = Image.open(src)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (250, 247, 244))
        im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    sw, sh = im.size
    sr = sw / sh
    if sr > ratio:                      # обрезаем по бокам
        nw = int(sh * ratio)
        im = im.crop(((sw - nw) // 2, 0, (sw - nw) // 2 + nw, sh))
    else:                              # обрезаем сверху/снизу
        nh = int(sw / ratio)
        im = im.crop((0, (sh - nh) // 2, sw, (sh - nh) // 2 + nh))
    im = im.resize((w, h), Image.LANCZOS)
    im.save(dst, "WEBP", quality=82, method=6)


def data_uri(path):
    with open(path, "rb") as f:
        return "data:image/webp;base64," + base64.b64encode(f.read()).decode("ascii")


def main():
    if len(sys.argv) < 2:
        sys.exit("Укажите папку с фото:  python вставить-свои-фото.py <путь>")
    folder = os.path.abspath(sys.argv[1])
    if not os.path.isdir(folder):
        sys.exit("Папка не найдена: " + folder)
    if not os.path.isfile(TEMPLATE):
        sys.exit("Рядом со скриптом нет папки site с шаблоном — держите их вместе.")

    work = os.path.join(folder, "_images")
    os.makedirs(work, exist_ok=True)

    used, missing = [], []
    for role, (w, h, ratio) in ROLES.items():
        src = find_photo(folder, role)
        if src:
            to_webp(src, os.path.join(work, role + ".webp"), w, h, ratio)
            used.append(role)
        else:
            shutil.copy(os.path.join(DEFAULT_IMAGES, role + ".webp"),
                        os.path.join(work, role + ".webp"))
            missing.append(role)

    html = open(TEMPLATE, encoding="utf-8").read()

    def repl(m):
        role = m.group(1)
        if role not in ROLES:
            return m.group(0)
        return 'src="data:image/webp;base64,%s"' % data_uri(os.path.join(work, role + ".webp")).split(",", 1)[1]

    html = re.sub(r'src="images/([a-z0-9\-]+)\.webp"', repl, html)
    hero = data_uri(os.path.join(work, "hero.webp"))
    html = html.replace("url('images/hero.webp')", "url('%s')" % hero)
    html = re.sub(r'content="images/hero\.webp"', 'content="%s"' % hero, html)

    out = os.path.join(folder, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print("Готово: " + out)
    print("Ваших фото вставлено: %d из %d" % (len(used), len(ROLES)))
    if missing:
        print("Остались демо-фото: " + ", ".join(missing))


if __name__ == "__main__":
    main()
