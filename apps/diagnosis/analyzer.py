import os
import numpy as np
from datetime import datetime
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
from django.conf import settings


# ── Jet colormap ─────────────────────────────────────────────────────────────

def _jet(t):
    t = float(np.clip(t, 0, 1))
    if t < 0.125:   r, g, b = 0,                   0,                 0.5 + t * 4
    elif t < 0.375: r, g, b = 0,                   (t-0.125)*4,       1.0
    elif t < 0.625: r, g, b = (t-0.375)*4,         1.0,               1.0-(t-0.375)*4
    elif t < 0.875: r, g, b = 1.0,                 1.0-(t-0.625)*4,   0
    else:           r, g, b = 1.0-(t-0.875)*4,     0,                 0
    return int(r*255), int(g*255), int(b*255)


def _jet_array(hm):
    t = np.clip(hm, 0, 1)
    r=np.zeros_like(t); g=np.zeros_like(t); b=np.zeros_like(t)
    def seg(lo,hi,fr,fg,fb):
        m=(t>=lo)&(t<hi); s=(t[m]-lo)/(hi-lo)
        r[m]=fr(s); g[m]=fg(s); b[m]=fb(s)
    seg(0,    0.125, lambda s:0,           lambda s:0,       lambda s:0.5+s*0.5)
    seg(0.125,0.375, lambda s:0,           lambda s:s,       lambda s:1.0)
    seg(0.375,0.625, lambda s:s,           lambda s:1.0,     lambda s:1.0-s)
    seg(0.625,0.875, lambda s:1.0,         lambda s:1.0-s,   lambda s:0)
    seg(0.875,1.001, lambda s:1.0-s*0.6,  lambda s:0,       lambda s:0)
    return np.stack([(r*255).clip(0,255),(g*255).clip(0,255),(b*255).clip(0,255)],2).astype(np.uint8)


def _gauss(h, w, cy, cx, sy, sx, amp=1.0):
    y, x = np.ogrid[:h, :w]
    return (amp * np.exp(-((y-cy*h)**2/(2*(sy*h)**2)+(x-cx*w)**2/(2*(sx*w)**2)))).astype(np.float32)


# ── Annotation callouts ───────────────────────────────────────────────────────

# (cy, cx, short_label, atrophy_pct, side, color_rgb)
_ANNOTATIONS = [
    (0.595, 0.305, 'R. Hippocampus', 68, 'R', (230, 60,  40)),   # strong red
    (0.595, 0.695, 'L. Hippocampus', 54, 'L', (235, 100, 40)),   # orange-red
    (0.660, 0.288, 'R. Entorhinal',  41, 'R', (200, 140, 30)),   # amber
    (0.660, 0.712, 'L. Entorhinal',  37, 'L', (200, 140, 30)),   # amber
]


def _draw_annotations(img_array, w, h, atrophy_values=None):
    """Draw medical callout labels on the blended result (numpy array → PIL → back).

    atrophy_values: optional list parallel to _ANNOTATIONS to override the
    hardcoded demo percentages with real, model-derived values.
    """
    img = Image.fromarray(img_array)
    draw = ImageDraw.Draw(img, 'RGBA')

    # Font — Pillow 10.x supports size parameter
    try:
        fs = max(11, min(16, h // 28))
        font_main  = ImageFont.load_default(size=fs)
        font_small = ImageFont.load_default(size=max(9, fs - 3))
    except TypeError:
        font_main = font_small = ImageFont.load_default()

    dot_r   = max(4, w // 90)        # hot-spot dot radius
    line_len = int(w * 0.17)          # callout line length

    for i, (cy, cx, label, atrophy, side, color) in enumerate(_ANNOTATIONS):
        if atrophy_values is not None:
            atrophy = atrophy_values[i]
        px, py = int(cx * w), int(cy * h)

        # ── hot-spot ring ──────────────────────────────────────────
        ring = dot_r + 3
        draw.ellipse([px-ring, py-ring, px+ring, py+ring],
                     outline=(*color, 220), width=2)
        draw.ellipse([px-dot_r, py-dot_r, px+dot_r, py+dot_r],
                     fill=(*color, 255))

        # ── callout line ───────────────────────────────────────────
        if side == 'R':
            lx = px - line_len
            txt_anchor = 'right'
        else:
            lx = px + line_len
            txt_anchor = 'left'
        ly = py
        draw.line([(px, py), (lx, ly)], fill=(*color, 200), width=1)
        draw.ellipse([lx-2, ly-2, lx+2, ly+2], fill=(*color, 220))

        # ── text badge ────────────────────────────────────────────
        line1 = label
        line2 = f"Atrophy {atrophy}%"
        pad = 4

        # measure text bounding box
        bb1 = draw.textbbox((0, 0), line1, font=font_main)
        bb2 = draw.textbbox((0, 0), line2, font=font_small)
        tw  = max(bb1[2]-bb1[0], bb2[2]-bb2[0])
        th  = (bb1[3]-bb1[1]) + (bb2[3]-bb2[1]) + pad

        if side == 'R':
            bx0 = lx - tw - pad*2
        else:
            bx0 = lx + pad

        by0 = ly - th // 2 - pad
        bx1, by1 = bx0 + tw + pad*2, by0 + th + pad*2

        # clamp to image bounds
        if bx0 < 2: bx0, bx1 = 2, bx1 + (2 - bx0)
        if bx1 > w-2: bx0, bx1 = w-2-(bx1-bx0), w-2
        if by0 < 2: by0, by1 = 2, by1 + (2 - by0)
        if by1 > h-2: by0, by1 = h-2-(by1-by0), h-2

        # semi-transparent dark background
        draw.rectangle([bx0, by0, bx1, by1], fill=(10, 10, 20, 195),
                       outline=(*color, 160), width=1)

        # text lines
        tx = bx0 + pad
        ty1 = by0 + pad
        ty2 = ty1 + (bb1[3] - bb1[1]) + 2
        draw.text((tx, ty1), line1, font=font_main,  fill=(255, 255, 255, 255))
        draw.text((tx, ty2), line2, font=font_small, fill=(*color, 240))

    return np.array(img.convert('RGB'))


# ── Grad-CAM generator ───────────────────────────────────────────────────────

def generate_gradcam(image_path):
    """
    Overlay a clinically-plausible MCI Grad-CAM with anatomical callouts
    on the real MRI. Returns the media URL of the saved PNG.
    """
    date_dir  = datetime.now().strftime('%Y/%m')
    out_dir   = os.path.join(str(settings.MEDIA_ROOT), 'heatmaps', date_dir)
    os.makedirs(out_dir, exist_ok=True)

    img_hash = str(abs(hash(image_path)))[-10:]
    fname    = f"gradcam_{img_hash}.png"
    out_path = os.path.join(out_dir, fname)

    if os.path.exists(out_path):
        return f"{settings.MEDIA_URL}heatmaps/{date_dir}/{fname}"

    # ── 1. Load ──────────────────────────────────────────────────────
    img = Image.open(image_path).convert('RGB')
    orig_w, orig_h = img.size
    scale = min(1.0, 640 / max(orig_w, orig_h))
    w, h  = int(orig_w * scale), int(orig_h * scale)
    img   = img.resize((w, h), Image.LANCZOS)

    # MRI aesthetic: grayscale + enhanced contrast
    gray = ImageEnhance.Contrast(img.convert('L')).enhance(2.2)
    gray = ImageEnhance.Brightness(gray).enhance(0.76)
    mri  = np.array(gray.convert('RGB')).astype(np.float32)

    # ── 2. Heatmap blobs (MCI signature) ─────────────────────────────
    hm = np.zeros((h, w), dtype=np.float32)
    #                           cy     cx     sy     sx    amp
    hm += _gauss(h,w,          0.595, 0.305, 0.072, 0.085, 1.00)  # R hippocampus
    hm += _gauss(h,w,          0.595, 0.695, 0.072, 0.085, 0.87)  # L hippocampus
    hm += _gauss(h,w,          0.660, 0.288, 0.050, 0.062, 0.64)  # R entorhinal
    hm += _gauss(h,w,          0.660, 0.712, 0.050, 0.062, 0.55)  # L entorhinal
    hm += _gauss(h,w,          0.648, 0.330, 0.038, 0.048, 0.50)  # R amygdala
    hm += _gauss(h,w,          0.648, 0.670, 0.038, 0.048, 0.42)  # L amygdala
    hm += _gauss(h,w,          0.635, 0.262, 0.033, 0.043, 0.35)  # R perirhinal
    hm += _gauss(h,w,          0.635, 0.738, 0.033, 0.043, 0.28)  # L perirhinal
    hm += _gauss(h,w,          0.420, 0.500, 0.082, 0.092, 0.28)  # Post. cingulate
    hm += _gauss(h,w,          0.380, 0.500, 0.054, 0.063, 0.18)  # Precuneus

    # organic noise
    rng = np.random.RandomState(seed=42)
    hm  = np.clip(hm + rng.randn(h, w).astype(np.float32) * 0.020, 0, None)
    hm /= hm.max()

    # ── 3. Smooth + punch ─────────────────────────────────────────────
    blur = max(w, h) * 0.013
    pil_hm = Image.fromarray((hm*255).astype(np.uint8), 'L')
    pil_hm = pil_hm.filter(ImageFilter.GaussianBlur(blur))
    pil_hm = pil_hm.filter(ImageFilter.GaussianBlur(blur * 0.4))
    hm = np.array(pil_hm).astype(np.float32) / 255.0
    hm = np.power(hm, 0.70)
    hm /= hm.max()

    # ── 4. Colormap + blend ───────────────────────────────────────────
    jet   = _jet_array(hm).astype(np.float32)
    alpha = np.clip((hm - 0.07) / 0.60, 0, 1)
    alpha = np.power(alpha, 0.78) * 0.82
    a3    = np.stack([alpha, alpha, alpha], 2)

    blended = np.clip(mri*(1-a3) + jet*a3, 0, 255).astype(np.uint8)

    # ── 5. Anatomical callout labels ──────────────────────────────────
    blended = _draw_annotations(blended, w, h)

    # ── 6. Scale back to original ─────────────────────────────────────
    result_img = Image.fromarray(blended).resize((orig_w, orig_h), Image.LANCZOS)

    # ── 7. Colorbar ───────────────────────────────────────────────────
    cb_h     = max(20, orig_h // 20)
    pad      = 8
    canvas_h = orig_h + cb_h + pad * 3 + 12
    canvas   = Image.new('RGB', (orig_w, canvas_h), (10, 10, 16))
    canvas.paste(result_img, (0, 0))

    draw   = ImageDraw.Draw(canvas)
    cb_y   = orig_h + pad
    margin = max(orig_w // 8, 24)
    x0, x1 = margin, orig_w - margin

    for i in range(x1 - x0):
        rv, gv, bv = _jet(i / (x1 - x0))
        draw.rectangle([x0+i, cb_y, x0+i+1, cb_y+cb_h], fill=(rv, gv, bv))
    draw.rectangle([x0-1, cb_y-1, x1+1, cb_y+cb_h+1], outline=(55,55,65), width=1)

    try:
        lbl_font = ImageFont.load_default(size=11)
    except TypeError:
        lbl_font = ImageFont.load_default()

    draw.text((x0+2,  cb_y+cb_h+3), "Low activation",  fill=(120,120,135), font=lbl_font)
    draw.text((x1-70, cb_y+cb_h+3), "High activation", fill=(220,80,60),   font=lbl_font)

    canvas.save(out_path, 'PNG', optimize=True)
    return f"{settings.MEDIA_URL}heatmaps/{date_dir}/{fname}"


# ── Real Grad-CAM (trained model) ────────────────────────────────────────────

def _sample_region_atrophy(hm, w, h):
    """Sample a real Grad-CAM heatmap at the same anatomical coordinates used
    for the demo callouts, so the regions table reflects actual model output."""
    values = []
    for cy, cx, *_ in _ANNOTATIONS:
        px, py = int(cx * w), int(cy * h)
        r = max(3, w // 60)
        y0, y1 = max(0, py - r), min(h, py + r)
        x0, x1 = max(0, px - r), min(w, px + r)
        patch = hm[y0:y1, x0:x1]
        values.append(int(np.clip(patch.mean() * 100, 0, 100)) if patch.size else 0)
    return values


def generate_real_gradcam(image_path, hm):
    """
    Render a real, model-derived Grad-CAM heatmap using the same visual style
    (jet colormap, anatomical callouts, colorbar) as the demo generate_gradcam().

    hm: 2D numpy array of any resolution, values in [0, 1] — raw Grad-CAM output.
    Returns (media_url, region_atrophy_values) so the caller can build a real
    regions table instead of the hardcoded demo percentages.
    """
    date_dir = datetime.now().strftime('%Y/%m')
    out_dir  = os.path.join(str(settings.MEDIA_ROOT), 'heatmaps', date_dir)
    os.makedirs(out_dir, exist_ok=True)

    img_hash = str(abs(hash(image_path)))[-10:]
    fname    = f"gradcam_real_{img_hash}.png"
    out_path = os.path.join(out_dir, fname)

    img = Image.open(image_path).convert('RGB')
    orig_w, orig_h = img.size
    scale = min(1.0, 640 / max(orig_w, orig_h))
    w, h  = int(orig_w * scale), int(orig_h * scale)
    img   = img.resize((w, h), Image.LANCZOS)

    gray = ImageEnhance.Contrast(img.convert('L')).enhance(2.2)
    gray = ImageEnhance.Brightness(gray).enhance(0.76)
    mri  = np.array(gray.convert('RGB')).astype(np.float32)

    hm_img = Image.fromarray((np.clip(hm, 0, 1) * 255).astype(np.uint8), 'L').resize((w, h), Image.BILINEAR)
    hm = np.array(hm_img).astype(np.float32) / 255.0
    if hm.max() > 0:
        hm = hm / hm.max()

    jet   = _jet_array(hm).astype(np.float32)
    alpha = np.clip((hm - 0.07) / 0.60, 0, 1)
    alpha = np.power(alpha, 0.78) * 0.82
    a3    = np.stack([alpha, alpha, alpha], 2)
    blended = np.clip(mri * (1 - a3) + jet * a3, 0, 255).astype(np.uint8)

    atrophy_values = _sample_region_atrophy(hm, w, h)
    blended = _draw_annotations(blended, w, h, atrophy_values=atrophy_values)

    result_img = Image.fromarray(blended).resize((orig_w, orig_h), Image.LANCZOS)

    cb_h     = max(20, orig_h // 20)
    pad      = 8
    canvas_h = orig_h + cb_h + pad * 3 + 12
    canvas   = Image.new('RGB', (orig_w, canvas_h), (10, 10, 16))
    canvas.paste(result_img, (0, 0))

    draw   = ImageDraw.Draw(canvas)
    cb_y   = orig_h + pad
    margin = max(orig_w // 8, 24)
    x0, x1 = margin, orig_w - margin

    for i in range(x1 - x0):
        rv, gv, bv = _jet(i / (x1 - x0))
        draw.rectangle([x0+i, cb_y, x0+i+1, cb_y+cb_h], fill=(rv, gv, bv))
    draw.rectangle([x0-1, cb_y-1, x1+1, cb_y+cb_h+1], outline=(55,55,65), width=1)

    try:
        lbl_font = ImageFont.load_default(size=11)
    except TypeError:
        lbl_font = ImageFont.load_default()

    draw.text((x0+2,  cb_y+cb_h+3), "Low activation",  fill=(120,120,135), font=lbl_font)
    draw.text((x1-70, cb_y+cb_h+3), "High activation", fill=(220,80,60),   font=lbl_font)

    canvas.save(out_path, 'PNG', optimize=True)
    url = f"{settings.MEDIA_URL}heatmaps/{date_dir}/{fname}"
    return url, atrophy_values


# ── Demo result ───────────────────────────────────────────────────────────────

DEMO_RESULT = {
    'result': 'MCI',
    'result_label': 'اختلال خفیف شناختی',
    'confidence': 67.4,
    'probabilities': [
        {'key': 'CN',  'label': 'سالم (CN)',     'value': 22.1, 'color': '#22c55e'},
        {'key': 'MCI', 'label': 'MCI خفیف',     'value': 67.4, 'color': '#f59e0b'},
        {'key': 'AD',  'label': 'آلزایمر (AD)', 'value': 10.5, 'color': '#ef4444'},
    ],
    'regions': [
        {'name': 'هیپوکامپوس راست',    'atrophy': 68, 'severity': 'متوسط',      'level': 'warning'},
        {'name': 'هیپوکامپوس چپ',     'atrophy': 54, 'severity': 'خفیف-متوسط', 'level': 'warning'},
        {'name': 'قشر آنتورینال راست', 'atrophy': 41, 'severity': 'خفیف',       'level': 'info'},
        {'name': 'قشر آنتورینال چپ',  'atrophy': 37, 'severity': 'خفیف',       'level': 'info'},
        {'name': 'آمیگدال راست',       'atrophy': 29, 'severity': 'خفیف',       'level': 'info'},
        {'name': 'قشر پری‌رینال',      'atrophy': 18, 'severity': 'طبیعی',      'level': 'success'},
        {'name': 'قشر پس‌کمربندی',     'atrophy': 14, 'severity': 'طبیعی',      'level': 'success'},
        {'name': 'لوب پیشانی',        'atrophy': 9,  'severity': 'طبیعی',      'level': 'success'},
    ],
    'risk_score': 62,
    'recommendation': (
        'بر اساس تحلیل تصویر MRI، الگویی سازگار با اختلال خفیف شناختی (MCI) مشاهده شده است. '
        'کاهش حجم دو‌طرفه در ناحیه هیپوکامپوس و قشر آنتورینال — دو منطقه کلیدی برای '
        'پردازش حافظه — قابل توجه است. آمیگدال راست نیز تغییرات خفیفی نشان می‌دهد. '
        'توصیه می‌شود ارزیابی‌های دوره‌ای هر ۶ ماه انجام شود و با متخصص مغز و اعصاب '
        'مشورت گردد.'
    ),
    'heatmap_url': '/static/images/demo-heatmap.png',
}


def analyze_mri(image_path=None):
    """
    Demo mode: returns fixed MCI result + dynamic Grad-CAM on the real image.
    Real mode (DEMO_MODE=False): runs the trained model from apps/diagnosis/ml/
    via ml_inference.analyze_mri_real() — see notebooks/alzheimer_model_training.ipynb.
    """
    if getattr(settings, 'DEMO_MODE', True):
        result = dict(DEMO_RESULT)
        if image_path and os.path.exists(image_path):
            result['heatmap_url'] = generate_gradcam(image_path)
        return result

    if not image_path:
        raise ValueError("image_path is required when DEMO_MODE is False.")

    from .ml_inference import analyze_mri_real
    return analyze_mri_real(image_path)
