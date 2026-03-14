"""生成 404 图片 → assets/pics/404.png（风格与 compose_images 一致）"""

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "./assets/fonts/line_seed_jietng.ttf"
LOGO_PATH = "./assets/pics/logo.png"
OUTPUT = "./assets/pics/404.png"

W, H = 600, 800

img = Image.new("RGB", (W, H), (255, 255, 255))
draw = ImageDraw.Draw(img)

# 字体
font_404 = ImageFont.truetype(FONT_PATH, 120)
font_sub = ImageFont.truetype(FONT_PATH, 28)
font_footer = ImageFont.truetype(FONT_PATH, 18)

# 404 主文字
draw.text((W // 2, H // 2 - 40), "404", font=font_404, fill=(0, 0, 0), anchor="mm")
draw.text((W // 2, H // 2 + 50), "Image Not Found", font=font_sub, fill=(100, 100, 100), anchor="mm")

# 页脚分割线
line_y = H - 80
draw.line([(40, line_y), (W - 40, line_y)], fill=(220, 220, 220), width=1)

# 页脚文字
draw.text((40, line_y + 15), "© JiETNG  |  Matsuki", font=font_footer, fill=(160, 160, 160))

# Logo（右下角）
try:
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_size = 45
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
    img.paste(logo, (W - 40 - logo_size, line_y + 8), logo)
except Exception:
    pass

# 圆角
from PIL import ImageDraw as ID

def round_corner(im, radius):
    mask = Image.new("L", im.size, 255)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), im.size], radius=radius, fill=255, outline=None)
    # 四角变透明
    corner_mask = Image.new("L", im.size, 0)
    cd = ImageDraw.Draw(corner_mask)
    cd.rounded_rectangle([(0, 0), im.size], radius=radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(corner_mask)
    return out

result = round_corner(img, 20)
result.save(OUTPUT)
print(f"Saved to {OUTPUT}")
