import requests
import json
import re
import sys
import time
import traceback
import os
import urllib.parse
import math
import difflib
import base64

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from config_loader import LOGO_PATH
from img_console import *

def get_difficulty_color(difficulty):
    colors = {
        "basic": (149, 207, 71),     # 绿色
        "advanced": (243, 162, 7),   # 黄色
        "expert": (255, 129, 141),   # 红色
        "master": (159, 81, 219),    # 紫色
        "remaster": (239, 224, 255), # 白色
        "utage": (245, 46, 221)      # 粉色
    }
    return colors.get(difficulty.lower(), (200, 200, 200))

def create_thumbnail(song, thumb_size=(300, 150), padding=15):
    bg_color = get_difficulty_color(song['difficulty'])
    img = Image.new("RGB", thumb_size, bg_color)
    draw = ImageDraw.Draw(img)

    text_color = (201, 123, 221) if song['difficulty'] == "remaster" else (255, 255, 255)

    # --- 封面 ---
    if 'url' in song and song['url']:
        try:
            response = requests.get(song['url'])
            cover_img = Image.open(BytesIO(response.content)).resize((80, 80))
            img.paste(cover_img, (padding, padding))
        except Exception as e:
            print(f"Error loading cover image: {e}")

    # --- kind 图标 ---
    paste_icon(
        img, song, key='kind',
        size=(40, 12),
        position=(padding + 80 - 40, padding + 80 - 12),
        save_dir='./config/icon/kind',
        url_func=lambda value: "https://maimaidx.jp/maimai-mobile/img/music_standard.png" if value == "std" else "https://maimaidx.jp/maimai-mobile/img/music_dx.png",
        verify=False
    )

    line_spacing = 28
    text_x_offset = padding + 90
    score_x_offset = thumb_size[0] - 20

    # --- 歌曲标题 ---
    max_text_width = thumb_size[0] - text_x_offset - 20
    truncated_name = truncate_text(draw, song['name'], font_large, max_text_width)
    draw.text((text_x_offset, padding - 5), truncated_name, fill=text_color, font=font_large)

    draw.line([(text_x_offset, padding + line_spacing - 2),
               (thumb_size[0] - padding, padding + line_spacing - 2)],
              fill=text_color, width=2)

    # --- 基础分数 ---
    draw.text((text_x_offset, padding + line_spacing), song['score'], fill=text_color, font=font_large)

    # --- score-icon 图标 ---
    paste_icon(
        img, song, key='score-icon',
        size=(65, 30),
        position=(score_x_offset - 60, padding + line_spacing),
        save_dir='./config/icon/score',
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_{value}.png",
        verify=False
    )

    # --- 版本标题 + dx-score ---
    draw.text((text_x_offset, padding + line_spacing * 2),
              song['version_title'].replace(" PLUS", "+").replace("でらっくす", "DX"),
              fill=text_color, font=font_small)

    draw.text((score_x_offset, padding + line_spacing * 2),
              song['dx-score'], fill=text_color, font=font_small, anchor="ra")

    # --- 最下面的横线 ---
    draw.line([(0, thumb_size[1]),
               (thumb_size[0], thumb_size[1])],
              fill=(255, 255, 255), width=90)

    # --- dx-star 星星图标 ---
    if 'dx-score' in song and song['dx-score']:
        try:
            dx_score = eval(song['dx-score'].replace(",", ""))
            if 0 <= dx_score < 0.85:
                star_num = 0
            elif 0.85 <= dx_score < 0.9:
                star_num = 1
            elif 0.9 <= dx_score < 0.93:
                star_num = 2
            elif 0.93 <= dx_score < 0.95:
                star_num = 3
            elif 0.95 <= dx_score < 0.97:
                star_num = 4
            elif 0.97 <= dx_score <= 1:
                star_num = 5

            paste_icon(
                img, {'star': str(star_num)}, key='star',
                size=(80, 16),
                position=(padding + 80, thumb_size[1] - 32),
                save_dir='./config/icon/dx-star',
                url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_dxstar_detail_{value}.png",
                verify=False
            )

        except Exception as e:
            print(f"Error calculating dx-star: {e}")

    # --- combo-icon 图标 ---
    paste_icon(
        img, song, key='combo-icon',
        size=(40, 45),
        position=(padding - 5, thumb_size[1] - 48),
        save_dir='./config/icon/combo',
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_{value}.png",
        verify=False
    )

    # --- dx-icon 图标 ---
    paste_icon(
        img, song, key='dx-icon',
        size=(40, 45),
        position=(padding + 40, thumb_size[1] - 48),
        save_dir='./config/icon/dx',
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_{value}.png",
        verify=False
    )


    # --- 名次和数值 ---
    draw.text((score_x_offset + 3, thumb_size[1] - 38),
              f"{song['internalLevelValue']:.1f} → {song['ra']}",
              fill=(0, 0, 0), font=font_large, anchor="ra")

    # --- 边框 ---
    border_color = (128, 128, 128)
    draw.rectangle([(0, 0), (thumb_size[0] - 1, thumb_size[1] - 1)], outline=border_color, width=5)

    final_img = img.convert("RGB")
    return final_img

def generate_records_picture(up_songs=[], down_songs=[], title="RECORD"):
    uploaded_data = up_songs + down_songs
    up_num = len(up_songs)
    down_num = len(down_songs)
    num = up_num + down_num

    if not num:
        return

    up_ra = down_ra = 0
    up_level = down_level = 0
    up_score = down_score = 0

    for rcd in up_songs :
        up_ra += rcd['ra']
        up_level += rcd['internalLevelValue']
        up_score += float(rcd['score'][:-1])

    for rcd in down_songs :
        down_ra += rcd['ra']
        down_level += rcd['internalLevelValue']
        down_score += float(rcd['score'][:-1])

    all_ra = up_ra + down_ra
    all_level = up_level + down_level
    all_score = up_score + down_score

    grid_size = (5, math.ceil(up_num / 5) + math.ceil(down_num / 5))
    thumb_size = (300, 150)
    footer_height = 155
    side_width = 20
    spacing = 10
    header_height = 190

    version_padding = 0 if not (up_songs and down_songs) else 20

    img_width = grid_size[0] * (thumb_size[0] + spacing) - spacing + side_width * 2
    img_height = header_height + grid_size[1] * (thumb_size[1] + spacing) + footer_height + version_padding + 30
    combined = Image.new("RGB", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(combined)

    header_text = [
        f"でらっくすレーティング:  {all_ra} = {up_ra} + {down_ra}",
        f"平均レーティング:  {round(float(all_ra)/num, 2):.2f}",
        f"平均レベル:  {round(float(all_level)/num, 2):.2f}",
        f"平均達成率:  {round(all_score/num, 4):.4f}%"
    ]

    draw_aligned_colon_text(
        draw,
        lines=header_text,
        top_left=(side_width + 20, side_width),  # 左上角起始坐标
        font=font_huge,
        spacing=7,
        fill=(0, 0, 0)
    )

    bbox = draw.textbbox((0, 0), title, font=font_huge_huge)
    title_width = bbox[2] - bbox[0]
    draw.text((img_width - side_width - title_width, -20), title, fill=(206, 206, 206), font=font_huge_huge)

    up_thumbnails = [create_thumbnail(song, thumb_size) for song in up_songs[:grid_size[0] * grid_size[1]]]
    down_thumbnails = [create_thumbnail(song, thumb_size) for song in down_songs[:grid_size[0] * grid_size[1]]]
    thumbnails = up_thumbnails + down_thumbnails

    for i, thumb in enumerate(up_thumbnails):
        x_offset = (i % grid_size[0]) * (thumb_size[0] + spacing) + side_width
        y_offset = header_height + (i // grid_size[0]) * (thumb_size[1] + spacing)
        combined.paste(thumb, (x_offset, y_offset))

    total_up_y_offset = header_height + ((up_num - 1) // grid_size[0]) * (thumb_size[1] + spacing)

    for i, thumb in enumerate(down_thumbnails):
        x_offset = (i % grid_size[0]) * (thumb_size[0] + spacing) + side_width
        y_offset = header_height + (i // grid_size[0]) * (thumb_size[1] + spacing) + version_padding + total_up_y_offset - spacing
        combined.paste(thumb, (x_offset, y_offset))

    footer_text = ["Generated by JiETNG.", "© 2025 Matsuki.", "All rights reserved."]
    for i, text in enumerate(footer_text):
        draw.text((side_width + 20, img_height - 150 + i * 35), text, fill=(0, 0, 0), font=font_huge)

    logo_img = Image.open(LOGO_PATH).resize((130, 130))
    combined.paste(logo_img, (img_width - 180, img_height - 150))

    return combined

def create_small_record(cover, icon, icon_type):
    img_width = 150
    img_height = 150
    record_img = Image.new("RGBA", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(record_img)

    response = requests.get(cover, verify=False)
    cover_img = Image.open(BytesIO(response.content)).resize((150, 150))
    record_img.paste(cover_img, (0, 0))

    if not icon == "back":
        try:
            file_path = f"./config/icon/{icon_type}/{icon}.png"
            if not os.path.exists(file_path):
                print(f"\n\n{file_path}\n\n")
                response = requests.get(f"https://maimaidx.jp/maimai-mobile/img/music_icon_{icon}.png", verify=False)
                with open(file_path, "wb") as f:
                    f.write(response.content)

            icon_img = Image.open(file_path)

            aspect_ratio = icon_img.height / icon_img.width
            new_height = int(130 * aspect_ratio)

            resized_img = icon_img.resize((130, new_height), Image.LANCZOS)

            x_offset = (record_img.width - 130) // 2
            y_offset = (record_img.height - new_height) // 2

            record_img.paste(resized_img, (x_offset, y_offset), resized_img.convert("RGBA"))

        except Exception as e:
            print(f"Error loading image from https://maimaidx.jp/maimai-mobile/img/music_icon_{icon}.png: {e}")

    return record_img

def generate_plate_image(target_data, img_width=1700, img_height=600, max_per_row=9, margin=20, headers={}):
    level_width = 100
    img_size = 150
    row_height = img_size + margin

    rows = []
    rows_num = 0
    level_list = ["15", "14+", "14", "13+", "13", "12+", "12", "11+", "11", "10+", "10"]
    for level in level_list:
        row_imgs = [entry["img"] for entry in target_data if entry["level"] == level]
        rows_num += math.ceil(len(row_imgs) / max_per_row)
        if row_imgs:
            rows.append((level, row_imgs))

    total_height = rows_num * row_height + margin + 170 + 190

    final_img = Image.new("RGB", (img_width, total_height), "white")
    draw = ImageDraw.Draw(final_img)

    add_ = 15
    for key, value in headers.items() :
        draw.text((margin + 50, margin + add_), f"{key.upper()}:", fill="black", font=font_huge)
        draw.text((margin + 350, margin + add_), f"{value['clear']} / {value['all']}", fill="black", font=font_huge)
        add_ += 40

    y_offset = margin + 30 + 180
    for level, img_list in rows:
        draw.text((margin, y_offset + img_size // 3), level, fill="black", font=font_for_plate)

        x_offset = level_width + margin  # 让图片靠右对齐
        for i, img in enumerate(img_list):
            if i > 0 and i % max_per_row == 0:
                y_offset += row_height  # 换行
                x_offset = level_width + margin  # 重新起点

            final_img.paste(img, (x_offset, y_offset))
            x_offset += img_size + margin

        y_offset += row_height  # 每个等级后换行

    footer_text = ["Generated by JiETNG.", "© 2025 Matsuki.", "All rights reserved."]
    for i, text in enumerate(footer_text):
        draw.text((margin + 20, total_height - 150 + i * 35), text, fill=(0, 0, 0), font=font_huge)

    logo_img = Image.open(LOGO_PATH).resize((130, 130))
    final_img.paste(logo_img, (img_width - 180, total_height - 150))

    return final_img
