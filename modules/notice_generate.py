import datetime
import os
from PIL import Image, ImageDraw, ImageFont
from config_loader import background_path, fonts_folder

font_path = os.path.join(fonts_folder, "biragino_w1.ttc")

def notice_generate(timestamp, lines):
    img = Image.open(background_path).convert('RGBA')
    draw = ImageDraw.Draw(img)

    main_font_size = 75
    time_font_size = 60
    line_font = ImageFont.truetype(font_path, size=main_font_size)
    time_font = ImageFont.truetype(font_path, size=time_font_size)

    dt = datetime.datetime.fromtimestamp(timestamp)
    time_str = f"{dt.year} · {dt.month:02d} · {dt.day:02d}"

    time_position = (120, 1240)
    draw.text(time_position, time_str, font=time_font, fill=(80, 80, 80, 255))

    start_x = 110  # 左边距
    start_y = 480  # 第一行起始高度
    line_spacing = 90  # 每行间距
    max_width = 1650  # 一行最大宽度

    current_y = start_y

    for raw_line in lines:
        prefix = "· "
        full_text = prefix + raw_line

        indent_bbox = draw.textbbox((0, 0), prefix, font=line_font)
        indent_width = indent_bbox[2] - indent_bbox[0]

        current_line = ""
        is_first_line = True

        for char in full_text:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=line_font)
            line_width = bbox[2] - bbox[0]

            if (start_x + line_width) <= (start_x + max_width):
                current_line = test_line
            else:
                draw.text(
                    (start_x if is_first_line else start_x + indent_width, current_y),
                    current_line,
                    font=line_font,
                    fill=(50, 50, 50, 255)
                )
                current_y += line_spacing
                current_line = char
                is_first_line = False

        if current_line:
            draw.text(
                (start_x if is_first_line else start_x + indent_width, current_y),
                current_line,
                font=line_font,
                fill=(50, 50, 50, 255)
            )
            current_y += line_spacing

    return img
