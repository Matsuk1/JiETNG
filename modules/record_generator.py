import math
import logging
import os

from PIL import Image, ImageDraw

from modules.config_loader import (
    LOGO_PATH,
    PLATES_DIR,
    ICON_TYPE_DIR,
    ICON_SCORE_DIR,
    ICON_DX_STAR_DIR,
    ICON_COMBO_DIR,
    ICON_SYNC_DIR,
    ICON_COMBO_RCD_DIR,
    ICON_SYNC_RCD_DIR,
    ICON_BASE_DIR
)
from modules.image_cache import *
from modules.image_manager import *

logger = logging.getLogger(__name__)

def _get_difficulty_color(difficulty):
    colors = {
        "basic": (117, 181, 32),     # 绿色
        "advanced": (239, 165, 8),   # 黄色
        "expert": (204, 77, 89),     # 红色
        "master": (159, 81, 220),    # 紫色
        "remaster": (233, 212, 243), # 白色
        "utage": (245, 46, 221)      # 粉色
    }
    return colors.get(difficulty.lower(), (200, 200, 200))

def create_thumbnail_in_line(song):
    thumb_size=(600, 225)
    bg_color = (255, 255, 255)
    img = Image.new("RGB", thumb_size, bg_color)
    draw = ImageDraw.Draw(img)

    text_color = (0, 0, 0)

    # --- 基础分数 ---
    dx_score = eval(song['dx_score'])
    draw.text((20, 0), song['score'], fill=text_color, font=font_record_name)
    draw.text((25, 72), f"{song['dx_score']} → {dx_score * 100:.1f}%", fill=text_color, font=font_record_info)

    # --- 游玩信息 ---
    if 'last_play_time' in song and 'play_count' in song:
        draw.text((25, 110), f"PC: {song['play_count']}", fill=text_color, font=font_record_info)
        draw.text((180, 110), f"Recent: {song['last_play_time']}", fill=text_color, font=font_record_info)

    # --- score_icon 图标 ---
    # 根据缩略图尺寸动态计算图标大小
    paste_icon_optimized(
        img, song, key='score_icon',
        size=(203, 90),
        position=(380, 20),
        save_dir=ICON_SCORE_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/playlog/{value.replace('p', 'plus')}.png"
    )

    # --- combo_icon 图标 ---
    paste_icon_optimized(
        img, song, key='combo_icon',
        size=(108, 56),
        position=(15, 156),
        save_dir=ICON_COMBO_RCD_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/playlog/{value.replace('back', 'fc_dummy').replace('fcp', 'fcplus').replace('app', 'applus')}.png"
    )

    # --- sync_icon 图标 ---
    paste_icon_optimized(
        img, song, key='sync_icon',
        size=(108, 56),
        position=(115, 156),
        save_dir=ICON_SYNC_RCD_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/playlog/{value.replace('back', 'sync_dummy').replace('fdx', 'fsd').replace('p', 'plus')}.png"
    )

    # --- dx_star 图标 ---
    if 'dx_score' in song and song['dx_score']:
        try:
            star_num = 0
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

            paste_icon_optimized(
                img, {'star': str(star_num)}, key='star',
                size=(164, 33),
                position=(227, 170),
                save_dir=ICON_DX_STAR_DIR,
                url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_dxstar_detail_{value}.png"
            )

        except Exception as e:
            logger.error(f"[RecordGenerator] ✗ Failed to calculate dx_star: error={e}")

    # --- 数值 ---
    draw.text((575, 165), f"{song['internalLevelValue']:.1f} → {song['ra']}", fill=(0, 0, 0), font=font_record_info, anchor="ra")

    # --- 边框 ---
    border_color = _get_difficulty_color(song['difficulty'])
    draw.rectangle([(0, 0), (thumb_size[0] - 1, thumb_size[1] - 1)], outline=border_color, width=7)

    final_img = img.convert("RGB")

    return final_img

def create_thumbnail(song, thumb_size=(300, 150), padding=15):
    bg_color = _get_difficulty_color(song['difficulty'])
    img = Image.new("RGB", thumb_size, bg_color)
    draw = ImageDraw.Draw(img)

    text_color = (114, 20, 141) if song['difficulty'] == "remaster" else (255, 255, 255)

    # --- 封面 ---
    # 根据缩略图尺寸动态计算封面大小
    cover_size = int(thumb_size[0] * 0.267)
    if 'cover_name' in song and song['cover_name']:
        try:
            cover_img = get_cover_image(
                cover_url=song.get('cover_url'),
                cover_name=song['cover_name']
            )
            if cover_img:
                cover_img = cover_img.resize((cover_size, cover_size), Image.Resampling.LANCZOS)
                cover_img = round_corner(cover_img, radius=8)
                img.paste(cover_img, (padding, padding), cover_img)
        except Exception as e:
            logger.error(f"[RecordGenerator] ✗ Failed to load cover image: error={e}")

    # --- type 图标 ---
    type_width = int(cover_size * 0.5)
    type_height = int(cover_size * 0.15)
    paste_icon_optimized(
        img, song, key='type',
        size=(type_width, type_height),
        position=(padding + cover_size - type_width, padding + cover_size - type_height),
        save_dir=ICON_TYPE_DIR,
        url_func=lambda value: "https://maimaidx.jp/maimai-mobile/img/music_standard.png" if value == "std" else "https://maimaidx.jp/maimai-mobile/img/music_dx.png" if value == "dx" else "https://maimaidx.jp/maimai-mobile/img/diff_utage.png"
    )

    # 根据缩略图尺寸动态计算布局
    line_spacing = int(thumb_size[1] * 0.187)
    text_x_offset = padding + cover_size + 10
    score_x_offset = thumb_size[0] - 15

    # --- 歌曲标题 ---
    max_text_width = thumb_size[0] - text_x_offset - 20
    truncated_name = truncate_text(draw, song['name'], font_stadium, max_text_width)
    draw.text((text_x_offset, padding - 5), truncated_name, fill=text_color, font=font_stadium)

    draw.line([(text_x_offset, padding + line_spacing - 2),
               (thumb_size[0] - padding, padding + line_spacing - 2)],
              fill=text_color, width=2)

    # --- 基础分数 ---
    draw.text((text_x_offset, padding + line_spacing), song['score'], fill=text_color, font=font_stadium)

    # --- score_icon 图标 ---
    # 根据缩略图尺寸动态计算图标大小
    score_icon_width = int(thumb_size[0] * 0.217)
    score_icon_height = int(thumb_size[1] * 0.2)
    paste_icon_optimized(
        img, song, key='score_icon',
        size=(score_icon_width, score_icon_height),
        position=(score_x_offset - score_icon_width + 5, padding + line_spacing),
        save_dir=ICON_SCORE_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/playlog/{value.replace('p', 'plus')}.png"
    )

    # --- 版本标题 + dx_score ---
    draw.text((text_x_offset, padding + line_spacing * 2),
              song['version'].replace(" PLUS", "+").replace("でらっくす", "DX"),
              fill=text_color, font=font_small)

    draw.text((score_x_offset, padding + line_spacing * 2),
              song['dx_score'], fill=text_color, font=font_small, anchor="ra")

    # --- 最下面的横线 ---
    draw.line([(0, thumb_size[1]), (thumb_size[0], thumb_size[1])], fill=(255, 255, 255), width=90)

    # --- dx_star 图标 ---
    if 'dx_score' in song and song['dx_score']:
        try:
            dx_score = eval(song['dx_score'])
            star_num = 0
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

            # 根据缩略图尺寸动态计算星星图标大小
            star_width = int(thumb_size[0] * 0.267)
            star_height = int(thumb_size[1] * 0.107)
            paste_icon_optimized(
                img, {'star': str(star_num)}, key='star',
                size=(star_width, star_height),
                position=(padding + cover_size, thumb_size[1] - int(thumb_size[1] * 0.213)),
                save_dir=ICON_DX_STAR_DIR,
                url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_dxstar_detail_{value}.png"
            )

        except Exception as e:
            logger.error(f"[RecordGenerator] ✗ Failed to calculate dx_star: error={e}")

    # --- combo_icon 图标 ---
    # 根据缩略图尺寸动态计算图标大小
    combo_icon_width = int(thumb_size[0] * 0.133)
    combo_icon_height = int(thumb_size[1] * 0.3)
    paste_icon_optimized(
        img, song, key='combo_icon',
        size=(combo_icon_width, combo_icon_height),
        position=(padding - 5, thumb_size[1] - int(thumb_size[1] * 0.32)),
        save_dir=ICON_COMBO_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_{value}.png"
    )

    # --- sync_icon 图标 ---
    paste_icon_optimized(
        img, song, key='sync_icon',
        size=(combo_icon_width, combo_icon_height),
        position=(padding + combo_icon_width - 5, thumb_size[1] - int(thumb_size[1] * 0.32)),
        save_dir=ICON_SYNC_DIR,
        url_func=lambda value: f"https://maimaidx.jp/maimai-mobile/img/music_icon_{value}.png"
    )


    # --- 数值 ---
    draw.text((score_x_offset + 3, thumb_size[1] - 38),
              f"{song['internalLevelValue']:.1f} → {song['ra']}",
              fill=(0, 0, 0), font=font_stadium, anchor="ra")

    # --- 边框 ---
    border_color = (220, 220, 220)
    draw.rectangle([(0, 0), (thumb_size[0] - 1, thumb_size[1] - 1)], outline=border_color, width=3)

    final_img = img.convert("RGB")
    return final_img

def generate_records_picture(up_songs=[], down_songs=[], title="RECORD", ver="jp"):
    uploaded_data = up_songs + down_songs
    up_num = len(up_songs)
    down_num = len(down_songs)
    num = up_num + down_num

    if not num:
        return

    up_ra = down_ra = 0
    up_level = down_level = 0
    up_score = down_score = 0

    for rcd in up_songs:
        up_ra += rcd['ra']
        up_level += rcd['internalLevelValue']
        up_score += float(rcd['score'][:-1])

    for rcd in down_songs:
        down_ra += rcd['ra']
        down_level += rcd['internalLevelValue']
        down_score += float(rcd['score'][:-1])

    all_ra = round(up_ra + down_ra, 2)
    all_level = up_level + down_level
    all_score = up_score + down_score

    grid_size = (5, math.ceil(up_num / 5) + math.ceil(down_num / 5))
    thumb_size = (300, 150)
    side_width = 20
    spacing = 10
    header_height = 245

    version_padding = 0 if not (up_songs and down_songs) else 40

    img_width = grid_size[0] * (thumb_size[0] + spacing) - spacing + side_width * 2
    img_height = header_height + grid_size[1] * (thumb_size[1] + spacing) + version_padding + 13
    combined = Image.new("RGB", (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(combined)

    if ver == "jp":
        header_text = [
            f"でらっくす RATING: {all_ra} = {up_ra} + {down_ra}" if up_ra and down_ra else f"でらっくす RATING: {all_ra}",
            f"平均レベル: {round(float(all_level)/num, 2):.2f}",
            f"平均達成率: {round(all_score/num, 4):.4f}%",
            f"平均レーティング: {round(float(all_ra)/num, 2):.2f}"
        ]
        
    else:
        header_text = [
            f"でらっくす RATING: {all_ra} = {up_ra} + {down_ra}" if up_ra and down_ra else f"でらっくす RATING: {all_ra}",
            f"AVG LEVEL: {round(float(all_level)/num, 2):.2f}",
            f"AVG ACHIEVEMENT: {round(all_score/num, 4):.4f}%",
            f"AVG RATING: {round(float(all_ra)/num, 2):.2f}"
        ]

    # 绘制统计信息背景卡片
    card_padding = 20
    card_x = side_width + 10
    card_y = side_width + 10

    left_texts = []
    right_texts = []
    for line in header_text:
        if ":" in line:
            left, right = line.split(":", 1)
            left_texts.append(left + ":")
            right_texts.append(right.strip())
        else:
            left_texts.append(line)
            right_texts.append("")

    # 计算左侧最大宽度
    max_left_width = max(draw.textbbox((0, 0), text, font=font_large)[2] for text in left_texts) + 10
    # 计算右侧最大宽度
    max_right_width = max(draw.textbbox((0, 0), text, font=font_large)[2] for text in right_texts) if right_texts else 0

    # 实际文本总宽度
    max_text_width = max_left_width + max_right_width

    line_height = draw.textbbox((0, 0), "JiETNG", font=font_large)[3]
    text_total_height = len(header_text) * (line_height + 7)

    # 根据实际文本宽度设置卡片宽度
    card_width = max_text_width + card_padding * 2
    card_height = text_total_height + card_padding * 2 - 10

    # 绘制带圆角的半透明背景框
    draw.rounded_rectangle(
        [card_x, card_y, card_x + card_width, card_y + card_height],
        radius=12,
        fill=(245, 248, 252),  # 淡蓝灰色背景
        outline=(200, 210, 225),  # 浅蓝灰色边框
        width=2
    )

    draw_aligned_colon_text(
        draw,
        lines=header_text,
        top_left=(card_x + card_padding, card_y + card_padding - 5),
        font=font_large,
        spacing=7,
        fill=(40, 40, 40)  # 深灰色文字
    )

    # 绘制标题
    bbox = draw.textbbox((0, 0), title, font=font_record_title)
    title_width = bbox[2] - bbox[0]
    title_x = img_width - side_width - title_width - 30
    title_y = card_y - 35
    draw.text((title_x, title_y), title, fill=(190, 190, 190), font=font_record_title)

    up_thumbnails = [create_thumbnail(song, thumb_size) for song in up_songs[:grid_size[0] * grid_size[1]]]
    down_thumbnails = [create_thumbnail(song, thumb_size) for song in down_songs[:grid_size[0] * grid_size[1]]]
    thumbnails = up_thumbnails + down_thumbnails

    for i, thumb in enumerate(up_thumbnails):
        x_offset = (i % grid_size[0]) * (thumb_size[0] + spacing) + side_width
        y_offset = header_height + (i // grid_size[0]) * (thumb_size[1] + spacing)
        combined.paste(thumb, (x_offset, y_offset))

    # 计算up部分最后一行的底部位置
    up_rows = math.ceil(up_num / grid_size[0])
    total_up_y_offset = header_height + up_rows * (thumb_size[1] + spacing)

    # 在上下部分中间绘制分隔线 (----·----) - 仅当同时有上下部分时显示
    if up_songs and down_songs:
        divider_y = total_up_y_offset + version_padding // 3 + 2
        divider_color = (140, 140, 140)

        # 计算中心点和线条长度
        center_x = img_width // 2
        line_half_length = (img_width - side_width * 2) // 2

        # 绘制左侧横线
        left_line_start = center_x - line_half_length // 2
        left_line_end = center_x - 10
        draw.line([(left_line_start, divider_y), (left_line_end, divider_y)], fill=divider_color, width=2)

        # 绘制中心点
        dot_radius = 3
        draw.ellipse([center_x - dot_radius, divider_y - dot_radius,
                     center_x + dot_radius, divider_y + dot_radius], fill=divider_color)

        # 绘制右侧横线
        right_line_start = center_x + 10
        right_line_end = center_x + line_half_length // 2
        draw.line([(right_line_start, divider_y), (right_line_end, divider_y)], fill=divider_color, width=2)

    for i, thumb in enumerate(down_thumbnails):
        x_offset = (i % grid_size[0]) * (thumb_size[0] + spacing) + side_width
        y_offset = total_up_y_offset + version_padding + (i // grid_size[0]) * (thumb_size[1] + spacing)
        combined.paste(thumb, (x_offset, y_offset))

    return combined


def generate_cover(cover_url, type, icon=None, icon_type=None, size=150, cover_name=None, complete_info=None, difficulty=None, achieved=None):
    """
    生成歌曲封面图片，带有类型标识和可选图标

    参数:
        cover_url: 封面 URL
        type: 歌曲类型 ("std" 或 "dx")
        icon: 可选的图标名称（如 "ap", "fc" 等）
        icon_type: 可选的图标类型（如 "combo", "score", "sync"）
        size: 封面尺寸（默认150）
        cover_name: 封面文件名（包含扩展名），优先使用本地文件
        difficulty: 难度名称（如 "basic", "advanced" 等），用于边框颜色
        achieved: 是否达成目标（True=已完成/False=未完成/None=不添加蒙层）
    """
    img_width = size
    img_height = size

    # 如果指定了难度，添加难度颜色边框
    border_width = 4 if difficulty else 0
    inner_size = size - border_width * 2

    # 创建底图
    if difficulty:
        # 使用难度颜色作为背景（边框）
        difficulty_color = _get_difficulty_color(difficulty)
        record_img = Image.new("RGB", (img_width, img_height), difficulty_color)
    else:
        record_img = Image.new("RGB", (img_width, img_height), (255, 255, 255))

    # 加载封面图片
    cover_img = get_cover_image(cover_url=cover_url, cover_name=cover_name)

    if cover_img:
        if difficulty:
            # 缩小封面，留出边框空间
            cover_img = cover_img.resize((inner_size, inner_size))
            record_img.paste(cover_img, (border_width, border_width))
        else:
            cover_img = cover_img.resize((size, size))
            record_img.paste(cover_img, (0, 0))

    # 添加 type 图标（std/dx）- 按比例缩放
    # 如果有 complete_info，放在右上角；否则放在右下角
    type_width = int(inner_size * 0.5) if difficulty else int(size * 0.5)
    type_height = int(inner_size * 0.15) if difficulty else int(size * 0.15)
    if complete_info is not None:
        # 有圆点信息时，type 放在右上角
        type_position = (img_width - type_width - border_width, border_width)
    else:
        # 无圆点信息时，type 放在右下角
        type_position = (img_width - type_width - border_width, img_height - type_height - border_width)

    paste_icon_optimized(
        record_img,
        {'type': type},
        key='type',
        size=(type_width, type_height),
        position=type_position,
        save_dir=ICON_TYPE_DIR,
        url_func=lambda value: "https://maimaidx.jp/maimai-mobile/img/music_standard.png" if value == "std" else "https://maimaidx.jp/maimai-mobile/img/music_dx.png"
    )

    # 检查底部是否有圆点容器
    has_bottom_content = False
    if complete_info:
        difficulties = ["basic", "advanced", "expert", "master"]
        has_bottom_content = any(complete_info.get(diff, False) for diff in difficulties)

    # 添加灰色蒙层（在 icon 之前，这样不会遮挡 icon）
    # 只有已完成的才添加灰色蒙层，未完成的保持原样
    if achieved is True:
        record_img = record_img.convert("RGBA")
        # 已完成：灰色蒙层
        overlay = Image.new("RGBA", record_img.size, (50, 50, 50, 180))
        record_img = Image.alpha_composite(record_img, overlay)

    # 如果提供了 icon 和 icon_type，显示对应的图标
    if icon and icon_type and icon != "back":
        try:
            file_path = f"{ICON_BASE_DIR}/{icon_type}/{icon}.png"
            url = f"https://maimaidx.jp/maimai-mobile/img/music_icon_{icon}.png"

            icon_img = download_and_cache_icon(url, file_path)
            if icon_img:
                # 转换为 RGBA 以支持透明度
                record_img = record_img.convert("RGBA")

                # 计算缩放 - 按比例缩放图标（考虑边框）
                base_size = inner_size if difficulty else size
                icon_width = int(base_size * 0.75)
                aspect_ratio = icon_img.height / icon_img.width
                new_height = int(icon_width * aspect_ratio)
                resized_img = icon_img.resize((icon_width, new_height), Image.Resampling.LANCZOS)

                # 阴影处理
                shadow = Image.new("RGBA", record_img.size, (0, 0, 0, 150))
                record_img = Image.alpha_composite(record_img, shadow)

                # 粘贴图标
                x_offset = (record_img.width - icon_width) // 2
                if has_bottom_content:
                    y_offset = (record_img.height - new_height) // 2 - int(base_size * 0.08)
                else:
                    y_offset = (record_img.height - new_height) // 2
                record_img.paste(resized_img, (x_offset, y_offset), resized_img.convert("RGBA"))

        except Exception as e:
            logger.error(f"[RecordGenerator] ✗ Failed to load icon: icon={icon}, error={e}")

    # 绘制难度完成情况小圆点
    if complete_info:
        # 所有难度列表
        difficulties = ["basic", "advanced", "expert", "master"]

        # 检查是否有任何难度为 True
        has_any_true = any(complete_info.get(diff, False) for diff in difficulties)

        # 只有当至少有一个难度为 True 时才绘制容器和圆点
        if has_any_true:
            record_img = record_img.convert("RGBA")
            draw = ImageDraw.Draw(record_img)

            # 圆点参数
            base_size = inner_size if difficulty else size
            dot_radius = int(base_size * 0.04 * 1.5)
            dot_y = img_height - dot_radius - int(base_size * 0.05) - border_width

            # 计算圆点间距和起始位置
            num_positions = len(difficulties)
            total_dots_width = (num_positions - 1) * (dot_radius * 4)  # 圆点之间的总宽度
            start_x = (img_width - total_dots_width) // 2  # 居中起始位置
            spacing_between = dot_radius * 4  # 圆点之间的间距

            # 绘制半透明灰白色背景容器
            container_padding_horizontal = int(dot_radius * 2.0)
            container_padding_vertical = int(dot_radius * 0.8) - 5
            container_x1 = start_x - container_padding_horizontal
            container_y1 = dot_y - dot_radius - container_padding_vertical
            container_x2 = start_x + total_dots_width + container_padding_horizontal
            container_y2 = dot_y + dot_radius + container_padding_vertical

            # 创建半透明容器层
            container_layer = Image.new("RGBA", record_img.size, (0, 0, 0, 0))
            container_draw = ImageDraw.Draw(container_layer)
            container_draw.rounded_rectangle(
                [container_x1, container_y1, container_x2, container_y2],
                radius=int(dot_radius * 0.8),
                fill=(240, 240, 240, 160)
            )

            # 将容器层合成到图像上
            record_img = Image.alpha_composite(record_img, container_layer)
            draw = ImageDraw.Draw(record_img)

            # 从左往右绘制小圆点
            for i, diff in enumerate(difficulties):
                if complete_info.get(diff, False):
                    # 如果该难度为 True，绘制对应颜色的圆点
                    color = _get_difficulty_color(diff)
                    dot_x = start_x + i * spacing_between

                    # 绘制圆点
                    draw.ellipse(
                        [dot_x - dot_radius, dot_y - dot_radius,
                         dot_x + dot_radius, dot_y + dot_radius],
                        fill=color
                    )
                # 如果为 False，留空

    return record_img.convert("RGB")

def generate_plate_image(target_data, title, img_width=1700, img_height=600, max_per_row=9, margin=20, headers={}):
    level_width = 100
    img_size = 150
    row_height = img_size + margin

    rows = []
    rows_num = 0
    level_list = ["15", "14+", "14", "13+", "13", "12+", "12", "11+", "11", "10+", "10"]
    for level in level_list:
        level_entries = [entry for entry in target_data if entry["level"] == level]
        # 按达成状态和达成率排序：已达成在前，未达成的按达成率从大到小
        level_entries.sort(key=lambda x: (not x.get("achieved", False), -x.get("achievement_rate", 0.0)))
        row_imgs = [entry["img"] for entry in level_entries]
        rows_num += math.ceil(len(row_imgs) / max_per_row)
        if row_imgs:
            rows.append((level, row_imgs))

    total_height = rows_num * row_height + margin + 170 + 40

    final_img = Image.new("RGB", (img_width, total_height), "white")
    draw = ImageDraw.Draw(final_img)

    # 绘制左侧信息栏：卡片式容器（2列布局）
    card_start_x = margin - 10
    card_y = margin + 15
    card_width = 325
    card_height = 65
    card_gap_x = 15  # 横向间距
    card_gap_y = 12  # 纵向间距
    border_width = 8

    final_img = final_img.convert("RGBA")

    for idx, (key, value) in enumerate(headers.items()):
        # 计算卡片位置
        row = idx % 2
        col = idx // 2
        card_x = card_start_x + col * (card_width + card_gap_x)
        current_y = card_y + row * (card_height + card_gap_y)

        # 获取难度对应的颜色
        difficulty_color = _get_difficulty_color(key)

        # 创建卡片层用于阴影和圆角
        card_layer = Image.new("RGBA", final_img.size, (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)

        # 绘制阴影效果
        shadow_offset = 3
        card_draw.rounded_rectangle(
            [card_x + shadow_offset, current_y + shadow_offset,
             card_x + card_width + shadow_offset, current_y + card_height + shadow_offset],
            radius=12,
            fill=(0, 0, 0, 30)
        )

        # 绘制卡片主体背景
        r, g, b = difficulty_color[:3]
        light_r = int(r + (255 - r) * 0.85)
        light_g = int(g + (255 - g) * 0.85)
        light_b = int(b + (255 - b) * 0.85)
        bg_color = (light_r, light_g, light_b, 255)

        card_draw.rounded_rectangle(
            [card_x, current_y, card_x + card_width, current_y + card_height],
            radius=12,
            fill=bg_color
        )

        # 绘制左侧彩色边框
        card_draw.rounded_rectangle(
            [card_x, current_y, card_x + border_width, current_y + card_height],
            radius=12,
            fill=difficulty_color + (255,) if len(difficulty_color) == 3 else difficulty_color
        )

        # 将卡片层合成到图像上
        final_img = Image.alpha_composite(final_img, card_layer)
        draw = ImageDraw.Draw(final_img)

        # 绘制难度名称
        text_x = card_x + border_width + 15
        text_y = current_y + (card_height - 30) // 2 - 5
        difficulty_text = f"{key.upper()}"
        draw.text((text_x, text_y), difficulty_text, fill=(60, 60, 60), font=font_large)

        # 判断是否全部完成
        is_completed = value['clear'] == value['all'] and value['all'] > 0

        # 绘制数据
        if is_completed:
            data_text = "✓"
        else:
            # 未完成时显示进度
            data_text = f"{value['clear']} / {value['all']}"

        data_text_width = draw.textlength(data_text, font=font_large)
        data_x = card_x + card_width - data_text_width - 15
        draw.text((data_x, text_y), data_text, fill=(40, 40, 40), font=font_large)

    final_img = final_img.convert("RGB")
    draw = ImageDraw.Draw(final_img)

    # 添加右侧标题（称号图片）
    try:
        plate_path = os.path.join(PLATES_DIR, f"{title}.webp")
        if os.path.exists(plate_path):
            plate_img = Image.open(plate_path).convert("RGBA")

            target_height = 160
            aspect_ratio = plate_img.width / plate_img.height
            target_width = int(target_height * aspect_ratio)
            plate_img = plate_img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            # 位置：右上角，横向中轴线不变
            plate_x = img_width - margin - target_width + 10
            original_center_y = margin + 90
            plate_y = original_center_y - target_height // 2

            # 贴上称号图片（支持透明）
            final_img.paste(plate_img, (plate_x, plate_y), plate_img)
        else:
            # 如果图片不存在，回退到文字显示
            title_text_size = draw.textlength(title, font=font_record_title)
            title_x = img_width - margin - title_text_size - 30
            title_y = margin - 25
            draw.text((title_x, title_y), title, fill=(206, 206, 206), font=font_record_title)
            logger.debug(f"[RecordGenerator] Plate image not found, using text: plate={title}")
    except Exception as e:
        # 出错时回退到文字显示
        title_text_size = draw.textlength(title, font=font_record_title)
        title_x = img_width - margin - title_text_size - 30
        title_y = margin - 25
        draw.text((title_x, title_y), title, fill=(206, 206, 206), font=font_record_title)
        logger.error(f"[RecordGenerator] ✗ Failed to load plate image: plate={title}, error={e}")

    # 渲染主体图像内容
    y_offset = margin + 30 + 180
    for level, img_list in rows:
        draw.text((margin, y_offset + img_size // 3), level, fill="black", font=font_level_badge)

        x_offset = level_width + margin
        for i, img in enumerate(img_list):
            if i > 0 and i % max_per_row == 0:
                y_offset += row_height
                x_offset = level_width + margin

            final_img.paste(img, (x_offset, y_offset))
            x_offset += img_size + margin

        y_offset += row_height

    return final_img


def generate_level_rank_progress_image(target_data, level_name, rank_name, stats, img_width=2700, max_per_row=15, margin=20):
    """
    生成难度评级进度图片，顶部显示总体统计卡片，下方显示按定数分组的封面列表

    参数:
        target_data: 歌曲数据列表，每个元素为 {"img": PIL.Image, "internal_level": float, "achieved": bool, "difficulty": str, "achievement_rate": float}
        level_name: 难度名称（如 "13", "13+", "14", "14+"）
        rank_name: 评级名称（如 "SSS⁺", "AP", "FDX"）
        stats: 统计信息字典 {"achieved": int, "unachieved": int, "unplayed": int, "total": int}
        img_width: 图片总宽度
        max_per_row: 每行最多显示的歌曲数量
        margin: 边距
    """
    level_width = 100
    img_size = 150
    row_height = img_size + margin

    # 统计卡片区域高度（2x2布局）
    card_area_height = 180

    all_data = target_data

    # 按照定数分组（降序），每组内已达成的排在前面
    rows = []
    total_rows = 0

    internal_levels = sorted(set(entry["internal_level"] for entry in all_data), reverse=True)

    for internal_level in internal_levels:
        level_str = f"{internal_level:.1f}"
        row_entries = [entry for entry in all_data if entry["internal_level"] == internal_level]

        # 按达成状态和达成率排序：已达成在前，未达成的按达成率从大到小
        # (not achieved, -achievement_rate)
        # achieved=True -> False -> 0, achieved=False -> True -> 1
        # 所以已达成的(0)会排在未达成的(1)前面
        # -achievement_rate 让达成率大的排在前面
        row_entries.sort(key=lambda x: (not x["achieved"], -x.get("achievement_rate", 0.0)))

        if row_entries:
            rows.append((level_str, row_entries))
            total_rows += math.ceil(len(row_entries) / max_per_row)

    # 计算总高度
    # 卡片总高度 = 2行卡片 + 中间间距
    cards_total_height = 2 * int(65 * 1.2) + int(12 * 1.2)
    # 总高度 = 顶部边距 + 卡片区域 + 卡片到内容间距 + 内容高度 + 底部边距
    total_height = margin + 15 + cards_total_height + 60 + total_rows * row_height + margin

    final_img = Image.new("RGB", (img_width, total_height), "white")
    draw = ImageDraw.Draw(final_img)

    # 绘制统计卡片
    card_start_x = margin + 5
    card_y = margin + 30
    card_width = 366
    card_height = 78
    card_gap_x = 18
    card_gap_y = 14
    border_width = 8

    # 四个统计卡片：完了、未完了、未プレイ、总计
    card_data = [
        ("完了", stats["achieved"], (76, 175, 80)),       # 绿色
        ("未完了", stats["unachieved"], (255, 152, 0)),   # 橙色
        ("未プレイ", stats["unplayed"], (158, 158, 158)),  # 灰色
        ("総計", stats["total"], (66, 133, 244))          # 蓝色
    ]

    final_img_rgba = final_img.convert("RGBA")

    for idx, (label, count, color) in enumerate(card_data):
        # 计算卡片位置（2列布局，先上下后左右）
        row = idx % 2
        col = idx // 2
        card_x = card_start_x + col * (card_width + card_gap_x)
        current_y = card_y + row * (card_height + card_gap_y)

        # 创建卡片层用于阴影和圆角
        card_layer = Image.new("RGBA", final_img_rgba.size, (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_layer)

        # 绘制阴影效果
        shadow_offset = 3
        card_draw.rounded_rectangle(
            [card_x + shadow_offset, current_y + shadow_offset,
             card_x + card_width + shadow_offset, current_y + card_height + shadow_offset],
            radius=12,
            fill=(0, 0, 0, 30)
        )

        # 绘制卡片主体背景（使用浅色版本）
        r, g, b = color
        light_r = int(r + (255 - r) * 0.85)
        light_g = int(g + (255 - g) * 0.85)
        light_b = int(b + (255 - b) * 0.85)
        bg_color = (light_r, light_g, light_b, 255)

        card_draw.rounded_rectangle(
            [card_x, current_y, card_x + card_width, current_y + card_height],
            radius=12,
            fill=bg_color
        )

        # 绘制左侧彩色边框
        card_draw.rounded_rectangle(
            [card_x, current_y, card_x + border_width, current_y + card_height],
            radius=12,
            fill=color + (255,)
        )

        # 将卡片层合成到图像上
        final_img_rgba = Image.alpha_composite(final_img_rgba, card_layer)
        card_draw = ImageDraw.Draw(final_img_rgba)

        # 绘制标签（左侧，边框后）
        text_x = card_x + border_width + 15
        text_y = current_y + (card_height - 30) // 2
        card_draw.text((text_x, text_y), label, fill=(60, 60, 60), font=font_large)

        # 绘制数量（右侧对齐）
        data_text = str(count)
        data_text_width = card_draw.textlength(data_text, font=font_large)
        data_x = card_x + card_width - data_text_width - 15
        card_draw.text((data_x, text_y), data_text, fill=(40, 40, 40), font=font_large)

    final_img = final_img_rgba.convert("RGB")
    draw = ImageDraw.Draw(final_img)

    # 绘制右侧标题
    if rank_name:
        title_text = f"{level_name} {rank_name} PROGRESS"
    else:
        title_text = f"{level_name} LEVEL LIST"
    title_text_size = draw.textlength(title_text, font=font_record_title)
    title_x = img_width - margin - title_text_size - 15
    title_y = 5
    draw.text((title_x, title_y), title_text, fill=(206, 206, 206), font=font_record_title)

    # 渲染主体图像内容
    cards_total_height = 2 * card_height + card_gap_y
    y_offset = card_y + cards_total_height + 40

    for level_str, entries_list in rows:
        draw.text((margin, y_offset + img_size // 3), level_str, fill="black", font=font_level_badge)

        x_offset = level_width + margin

        for i, entry in enumerate(entries_list):
            if i > 0 and i % max_per_row == 0:
                y_offset += row_height
                x_offset = level_width + margin

            cover_img = entry["img"]
            final_img.paste(cover_img, (x_offset, y_offset))
            x_offset += img_size + margin

        y_offset += row_height

    return final_img
