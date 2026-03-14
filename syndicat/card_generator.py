"""
Génération de cartes de membre (RECTO + VERSO) en PNG.
Adapté pour e-Syndicat (Member, Syndicat).
"""

import os
from datetime import date
from io import BytesIO

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageOps


def _find_asset(*paths):
    """Trouve le premier chemin existant parmi les candidats."""
    base = settings.BASE_DIR
    for p in paths:
        full = base / p if isinstance(base, os.PathLike) else os.path.join(base, p)
        if os.path.exists(full):
            return str(full)
    return None


def _extract_brand_blues(logo_path, default_primary=(12, 74, 110), default_accent=(30, 64, 175)):
    """Extrait des couleurs de marque depuis un logo, ou retourne des défauts."""
    if not logo_path or not os.path.exists(logo_path):
        return default_primary, default_accent
    try:
        img = Image.open(logo_path).convert("RGB")
        img = img.resize((50, 50))
        pixels = list(img.getdata())
        blues = [p for p in pixels if p[2] > p[0] and p[2] > p[1]]
        if blues:
            r = sum(p[0] for p in blues) // len(blues)
            g = sum(p[1] for p in blues) // len(blues)
            b = sum(p[2] for p in blues) // len(blues)
            primary = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            accent = (max(0, min(255, r + 20)), max(0, min(255, g + 20)), max(0, min(255, b + 30)))
            return primary, accent
    except Exception:
        pass
    return default_primary, default_accent


def _draw_soft_gradient(img, primary, accent):
    """Applique un dégradé doux sur l'image."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(h):
        t = y / h
        r = int(primary[0] * (1 - t) + 245 * t)
        g = int(primary[1] * (1 - t) + 247 * t)
        b = int(primary[2] * (1 - t) + 250 * t)
        d.line([(0, y), (w, y)], fill=(r, g, b, 30))
    img.paste(Image.blend(img.convert("RGBA"), overlay, 0.15).convert("RGB"), (0, 0))
    return img


def _resize_to_card(bg, width, height):
    """Redimensionne l'image pour remplir exactement la taille de la carte (cover)."""
    ratio = max(width / bg.width, height / bg.height)
    new_w = int(bg.width * ratio)
    new_h = int(bg.height * ratio)
    bg = bg.resize((new_w, new_h), Image.LANCZOS)
    left = (bg.width - width) // 2
    top = (bg.height - height) // 2
    return bg.crop((left, top, left + width, top + height))


def _load_font(size, bold=False):
    """Charge une police (fallback si PIL n'a pas de font)."""
    try:
        from PIL import ImageFont
        base = getattr(settings, "BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if hasattr(base, "__fspath__"):
            base = str(base)
        for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf", "Arial.ttf"):
            for d in ["fonts", "font", "static/fonts", "syndicat/static/fonts", ""]:
                path = os.path.join(base, d, name) if d else os.path.join(base, name)
                if os.path.exists(path):
                    return ImageFont.truetype(path, size)
        # Essayer les polices système
        for fname in ("arial.ttf", "Arial Bold.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(fname, size)
            except OSError:
                continue
    except Exception:
        pass
    return ImageFont.load_default()


def generate_card_image(member_id):
    """
    Génère une carte de membre professionnelle (RECTO + VERSO) en PNG.
    Utilise les couleurs du logo du syndicat.
    Sauvegarde generated_card (RECTO) et generated_card_back (VERSO) sur le Member.
    Retourne l'URL de la carte RECTO.
    """
    from .models import Member

    member = Member.objects.select_related("syndicat", "categorie", "matricule").get(id=member_id)
    syndicat = member.syndicat

    chief_title = syndicat.signataire_titre or "Le Président"
    chief_name = syndicat.signataire_nom or ""
    chief_sig_path = None
    if syndicat.cachet and hasattr(syndicat.cachet, "path"):
        try:
            chief_sig_path = syndicat.cachet.path
        except (ValueError, AttributeError):
            chief_sig_path = None

    WIDTH = 1016
    HEIGHT = 638

    logo_syndicat = None
    if syndicat.logo and hasattr(syndicat.logo, "path"):
        try:
            if os.path.exists(syndicat.logo.path):
                logo_syndicat = syndicat.logo.path
        except (ValueError, AttributeError):
            pass
    if not logo_syndicat:
        logo_syndicat = _find_asset("syndicat/static/logo.png", "static/logo.png", "media/logo.png")

    primary, accent = _extract_brand_blues(logo_syndicat)

    # --- RECTO ---
    image_fond_recto_path = None
    if syndicat.image_fond and hasattr(syndicat.image_fond, "path"):
        try:
            if os.path.exists(syndicat.image_fond.path):
                image_fond_recto_path = syndicat.image_fond.path
        except (ValueError, AttributeError):
            pass
    if image_fond_recto_path:
        bg = Image.open(image_fond_recto_path).convert("RGB")
        recto = _resize_to_card(bg, WIDTH, HEIGHT)
        filigrane = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 235))
        recto = Image.alpha_composite(recto.convert("RGBA"), filigrane).convert("RGB")
    else:
        recto = Image.new("RGB", (WIDTH, HEIGHT), (250, 251, 253))
        recto = _draw_soft_gradient(recto, primary, accent)
    dr = ImageDraw.Draw(recto)

    pad = 44
    font_title = _load_font(42, bold=True)
    font_meta = _load_font(34, bold=False)
    font_meta_b = _load_font(34, bold=True)
    font_val = _load_font(30, bold=True)

    title_bbox = dr.textbbox((0, 0), syndicat.nom.upper(), font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (WIDTH - title_w) // 2
    title_y = pad + 8
    shadow_offset = 2
    dr.text((title_x + shadow_offset, title_y + shadow_offset), syndicat.nom.upper(), font=font_title, fill=(100, 110, 130))
    dr.text((title_x + 1, title_y + 1), syndicat.nom.upper(), font=font_title, fill=(60, 70, 90))
    dr.text((title_x, title_y), syndicat.nom.upper(), font=font_title, fill=(30, 35, 50))

    full_name = f"{member.nom} {member.postnom} {member.prenom}".strip() or "Nom Prénom"
    photo_size = 240
    photo_x = WIDTH - pad - photo_size - 30
    photo_y = pad + 65
    max_text_width = photo_x - pad - 30

    name_font_size = 38
    name_font = _load_font(name_font_size, bold=True)
    bbox = dr.textbbox((0, 0), full_name, font=name_font)
    text_width = bbox[2] - bbox[0]
    while text_width > max_text_width and name_font_size > 22:
        name_font_size -= 2
        name_font = _load_font(name_font_size, bold=True)
        bbox = dr.textbbox((0, 0), full_name, font=name_font)
        text_width = bbox[2] - bbox[0]
    dr.text((pad, pad + 75), full_name, font=name_font, fill=(30, 35, 50))

    position = member.categorie.nom if member.categorie else ""
    if position:
        dr.text((pad, pad + 130), position, font=_load_font(34, bold=True), fill=(60, 70, 90))

    left_x = pad
    base_y = pad + 175
    line_h = 54

    category = member.categorie.nom if member.categorie else ""
    edu = member.ministere_entreprise or ""
    matricule = (member.matricule or member.numero_membre) or ""
    date_du_jour = date.today().strftime("%d/%m/%Y")

    qr_payload = f"{member.prenom}|{member.nom}|{matricule}|{category}"
    qr_size_recto = 120
    qr_recto_x = (WIDTH - qr_size_recto) // 2
    qr_recto_y = HEIGHT - pad - qr_size_recto - 16
    try:
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(qr_payload)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.convert("RGB")
        qr_img = qr_img.resize((qr_size_recto, qr_size_recto), Image.LANCZOS)
        recto.paste(qr_img, (qr_recto_x, qr_recto_y))
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("QR code generation failed: %s", e)

    adresse = member.adresse or ""
    info_rows = [
        ("Matricule", matricule),
        ("Catégorie", category),
        ("Min./Entr.", edu),
        ("Adresse", adresse),
        ("Kinshasa, le", date_du_jour),
    ]

    sample = "Ag"
    bbox = dr.textbbox((0, 0), sample, font=font_meta)
    text_h = bbox[3] - bbox[1]
    val_x = left_x + 220
    max_val_width = photo_x - val_x - 20

    def _wrap_text(text, font, max_px):
        words = (text or "-").split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip() if cur else w
            bb = dr.textbbox((0, 0), test, font=font)
            if (bb[2] - bb[0]) <= max_px:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or ["-"]

    for i, (k, v) in enumerate(info_rows):
        row_offset = line_h if i > 3 else 0
        row_y = base_y + i * line_h + row_offset
        if k == "Adresse":
            lines = _wrap_text(v, font_val, max_val_width)[:2]
            dr.text((left_x, row_y), f"{k} :", font=font_meta_b, fill=(50, 55, 70))
            val_h = dr.textbbox((0, 0), "Ag", font=font_val)[3] - dr.textbbox((0, 0), "Ag", font=font_val)[1]
            for j, ln in enumerate(lines):
                dr.text((val_x, row_y + j * (val_h + 4)), ln, font=font_val, fill=(20, 55, 130))
        else:
            text_y = row_y + (line_h - text_h) // 2
            dr.text((left_x, text_y), f"{k} :", font=font_meta_b, fill=(50, 55, 70))
            dr.text((val_x, text_y), (v or "-")[:28], font=font_val, fill=(20, 55, 130))

    shadow = Image.new("RGBA", (photo_size + 20, photo_size + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((0, 0, photo_size + 20, photo_size + 20), radius=30, fill=(0, 0, 0, 60))
    recto.paste(shadow, (photo_x - 10, photo_y - 10), shadow)

    frame = Image.new("RGBA", (photo_size + 8, photo_size + 8), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle((0, 0, photo_size + 8, photo_size + 8), radius=28, fill=(255, 255, 255), outline=(180, 185, 195), width=2)
    recto.paste(frame, (photo_x - 4, photo_y - 4), frame)

    if member.photo and hasattr(member.photo, "path") and os.path.exists(member.photo.path):
        ph = Image.open(member.photo.path)
    else:
        ph = Image.new("RGB", (photo_size, photo_size), (235, 238, 245))
        pdraw = ImageDraw.Draw(ph)
        pdraw.rounded_rectangle((40, 40, photo_size - 40, photo_size - 40), radius=20, outline=(200, 205, 220), width=6)

    ph = ImageOps.fit(ph, (photo_size, photo_size), method=Image.LANCZOS, centering=(0.5, 0.2))
    mask = Image.new("L", (photo_size, photo_size), 0)
    m = ImageDraw.Draw(mask)
    m.rounded_rectangle((0, 0, photo_size, photo_size), radius=26, fill=255)
    recto.paste(ph, (photo_x, photo_y), mask)

    info_top = photo_y + photo_size + 18
    info_left = photo_x
    info_w = photo_size
    font_chief = _load_font(24, bold=True)
    dr.text((info_left, info_top), chief_title, font=font_chief, fill=(50, 55, 70))
    bbox = dr.textbbox((info_left, info_top), chief_title, font=font_chief)
    x1, y1, x2, y2 = bbox
    underline_y = y2 + 4
    dr.line((x1, underline_y, x2, underline_y), fill=(80, 90, 100), width=2)
    if chief_name.strip():
        dr.text((info_left, info_top + 28), chief_name.strip(), font=_load_font(26, bold=True), fill=(40, 45, 60))
    if chief_sig_path and os.path.exists(chief_sig_path):
        try:
            sig = Image.open(chief_sig_path).convert("RGBA")
            cachet_w, cachet_h = info_w * 3, 70 * 3
            sig = ImageOps.contain(sig, (cachet_w, cachet_h), Image.LANCZOS)
            sig_x = WIDTH - pad - sig.size[0] - 5
            sig_y = info_top + 20
            recto.paste(sig, (sig_x, sig_y), sig)
        except Exception:
            pass

    # --- VERSO ---
    image_fond_verso_path = None
    if syndicat.image_fond_verso and hasattr(syndicat.image_fond_verso, "path"):
        try:
            if os.path.exists(syndicat.image_fond_verso.path):
                image_fond_verso_path = syndicat.image_fond_verso.path
        except (ValueError, AttributeError):
            pass
    if image_fond_verso_path:
        bg = Image.open(image_fond_verso_path).convert("RGB")
        verso = _resize_to_card(bg, WIDTH, HEIGHT)
    else:
        verso = Image.new("RGB", (WIDTH, HEIGHT), (245, 246, 248))
        verso = _draw_soft_gradient(verso, primary, accent)
    dv = ImageDraw.Draw(verso)

    row_top = pad + 80

    sentence = syndicat.clause_legale or "Les autorités civiles et militaires sont priées d'apporter toute leur assistance au porteur de la présente."
    font_sentence = _load_font(32, bold=False)
    max_text_w = WIDTH - (pad * 2) - 120
    words = sentence.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bb = dv.textbbox((0, 0), test, font=font_sentence)
        if (bb[2] - bb[0]) <= max_text_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    line_height = 10
    total_h = sum(dv.textbbox((0, 0), ln, font=font_sentence)[3] - dv.textbbox((0, 0), ln, font=font_sentence)[1] + line_height for ln in lines) - line_height
    text_start_y = HEIGHT - pad - total_h - 24
    band_top = text_start_y - 12
    band_bottom = HEIGHT
    band = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    band_draw = ImageDraw.Draw(band)
    band_draw.rectangle((0, band_top, WIDTH, band_bottom), fill=(0, 0, 0, 100))
    verso = Image.alpha_composite(verso.convert("RGBA"), band).convert("RGB")
    dv = ImageDraw.Draw(verso)
    y = text_start_y
    fill_clause = (255, 255, 255)
    for ln in lines:
        bb = dv.textbbox((0, 0), ln, font=font_sentence)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        x = (WIDTH - tw) // 2
        dv.text((x, y), ln, font=font_sentence, fill=fill_clause)
        y += th + line_height

    # --- Sauvegarde ---
    output_recto = BytesIO()
    recto.save(output_recto, format="PNG", optimize=True)
    output_verso = BytesIO()
    verso.save(output_verso, format="PNG", optimize=True)

    if member.generated_card:
        member.generated_card.delete(save=False)
    if member.generated_card_back:
        member.generated_card_back.delete(save=False)

    member.generated_card.save(f"card_{member.id}_recto.png", ContentFile(output_recto.getvalue()), save=False)
    member.generated_card_back.save(f"card_{member.id}_verso.png", ContentFile(output_verso.getvalue()), save=True)
    member.save()

    return member.generated_card.url
