"""
Làm nét + làm đậm ảnh ERD pgAdmin (erd_v2.png) MÀ KHÔNG vẽ lại, không thêm gì.
Pipeline: upscale 2x (Lanczos) -> làm đậm nét chữ (min-filter) -> tăng tương phản
          -> unsharp mask. Giữ nguyên 100% bố cục, bảng, cột, liên kết.

Output: docs/diagrams/erd_v2_sharp.png
"""
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'docs' / 'diagrams' / 'erd_v2.png'
DST  = ROOT / 'docs' / 'diagrams' / 'erd_v2_sharp.png'

SCALE = 2  # phóng to 2x để in nét

img = Image.open(SRC).convert('RGB')
w, h = img.size
print(f'Goc: {w}x{h}')

# 1. Upscale 2x bằng Lanczos (thuat toan resample chat luong cao)
img = img.resize((w * SCALE, h * SCALE), Image.LANCZOS)

# 2. Lam dam net chu/duong: MinFilter lam day cac pixel toi (chu den tren nen trang)
#    size=3 tren anh da phong to => net chu day len mot chut, khong vo
img = img.filter(ImageFilter.MinFilter(3))

# 3. Tang tuong phan => chu xam nhat thanh dam hon, nen trang sach hon
img = ImageEnhance.Contrast(img).enhance(1.35)

# 4. Unsharp mask => vien chu/duong sac net
img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=160, threshold=2))

# Luu o 300 DPI de chen bao cao in net
img.save(DST, dpi=(300, 300))
print(f'Xong: {DST}  ({img.size[0]}x{img.size[1]})')
