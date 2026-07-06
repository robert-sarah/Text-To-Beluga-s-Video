from PIL import Image, ImageFont, ImageDraw
from pilmoji import Pilmoji
import sys
import datetime
import os
import json
import random
import regex
import re

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QFileDialog

from script_validator import parse_script

BASE_DIR = os.path.dirname(__file__)
CHAT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'chat'))
PROFILE_PICS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'profile_pictures'))
FONT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'fonts'))
URL_PATTERN = re.compile(r'(https?://[^\s]+|www\.[^\s]+)')

# CONSTANTS
WORLD_WIDTH = 1777
WORLD_Y_INIT_MESSAGE = 231
WORLD_DY = 70
WORLD_COLOR = (54, 57, 63, 255)

WORLD_HEIGHT_JOINED = 100
JOINED_FONT_SIZE = 45
JOINED_FONT_COLOR = (157, 161, 164)
JOINED_TEXTS = [
    "CHARACTER joined the party.",
    "CHARACTER is here.",
    "Welcome, CHARACTER. We hope you brought pizza.",
    "A wild CHARACTER appeared.",
    "CHARACTER just landed.",
    "CHARACTER just slid into the server.",
    "CHARACTER just showed up.",
    "Welcome CHARACTER. Say hi!",
    "CHARACTER hopped into the server.",
    "Everyone welcome CHARACTER!",
    "Glad you're here, CHARACTER!",
    "Good to see you, CHARACTER!",
    "Yay you made it, CHARACTER!",
]

PROFPIC_WIDTH = 120
PROFPIC_POSITION = (36, 45)

NAME_FONT_SIZE = 50
TIME_FONT_SIZE = 40
MESSAGE_FONT_SIZE = 50
NAME_FONT_COLOR = (255, 255, 255)
TIME_FONT_COLOR = (148, 155, 164)
MESSAGE_FONT_COLOR = (220, 222, 225)
NAME_POSITION = (190, 53)
TIME_POSITION_Y = 67  # X to be determined from name length
NAME_TIME_SPACING = 25
MESSAGE_X = 190
MESSAGE_Y_INIT = 115
MESSAGE_DY = 70

# Load fonts
font = "whitney" # Change this according to the font you want to use
name_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'semibold.ttf'), NAME_FONT_SIZE)
time_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'semibold.ttf'), TIME_FONT_SIZE)
message_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'medium.ttf'), MESSAGE_FONT_SIZE)
message_italic_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'medium_italic.ttf'), MESSAGE_FONT_SIZE)
message_bold_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'bold.ttf'), MESSAGE_FONT_SIZE)
message_italic_bold_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'bold_italic.ttf'), MESSAGE_FONT_SIZE)
message_mention_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'semibold.ttf'), MESSAGE_FONT_SIZE)
message_mention_italic_font = ImageFont.truetype(os.path.join(FONT_DIR, font, 'semibold_italic.ttf'), MESSAGE_FONT_SIZE)

# Load profile picture dictionary
with open(os.path.join(PROFILE_PICS_DIR, 'characters.json'), encoding="utf8") as file:
    characters_dict = json.load(file)

# Default profile used when a character is not defined in characters.json
DEFAULT_PROFILE = {
    "profile_pic": os.path.join('perm', 'nerd.jpg'),
    "role_color": NAME_FONT_COLOR,
}


def is_emoji_message(message):
    """Return True if the message contains only emoji characters."""
    return bool(message) and all(regex.match(r'^\p{Emoji}+$', char) for char in message.strip())


def _get_text_width(font_used, text):
    bbox = font_used.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_text_part(draw_template, pilmoji, text, font_used, current_x, y_pos, color, strike=False, is_url=False):
    pilmoji.text((current_x, y_pos), text, color, font=font_used,
                 emoji_position_offset=(0, 8), emoji_scale_factor=1.2)
    width, height = _get_text_width(font_used, text)
    if strike:
        line_y = y_pos + height // 2
        draw_template.line((current_x, line_y, current_x + width, line_y),
                           fill=color, width=max(1, MESSAGE_FONT_SIZE // 12))
    if is_url:
        underline_y = y_pos + height - 8
        draw_template.line((current_x, underline_y, current_x + width, underline_y),
                           fill=color, width=max(1, MESSAGE_FONT_SIZE // 18))
    return width


def generate_chat(messages, name_time, profpic_file, color):
    """
    Generates a chat image given the list of messages, name & time info,
    profile picture file, and a role color.
    """
    name_text = name_time[0]
    time_text = f'Today at {name_time[1]} PM'
    
    # Calculate baseline-aligned time position
    name_ascent, _ = name_font.getmetrics()
    time_ascent, _ = time_font.getmetrics()
    baseline_y = NAME_POSITION[1] + name_ascent
    time_position = (
        NAME_POSITION[0] + name_font.getbbox(name_text)[2] + NAME_TIME_SPACING,
        baseline_y - time_ascent
    )
    
    # Open and process profile picture
    prof_pic = Image.open(profpic_file)
    prof_pic.thumbnail((sys.maxsize, PROFPIC_WIDTH), Image.ANTIALIAS)
    mask = Image.new("L", prof_pic.size, 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (PROFPIC_WIDTH, PROFPIC_WIDTH)], fill=255)
    
    # Calculate required vertical height based on message count and spacing.
    visible_messages = [msg for msg in messages if msg.strip()]
    total_height = MESSAGE_Y_INIT + len(visible_messages) * MESSAGE_DY
    emoji_extra = 0
    for msg in visible_messages:
        if is_emoji_message(msg):
            bbox = message_font.getbbox("💀")
            emoji_extra += (bbox[3] - bbox[1]) + 8
    total_height += emoji_extra

    template = Image.new(mode='RGBA', size=(WORLD_WIDTH, total_height), color=WORLD_COLOR)
    template.paste(prof_pic, PROFPIC_POSITION, mask)
    draw_template = ImageDraw.Draw(template)
    
    draw_template.text(NAME_POSITION, name_text, color, font=name_font)
    draw_template.text(time_position, time_text, TIME_FONT_COLOR, font=time_font)

    y_offset = 0
    for i, message in enumerate(visible_messages):
        message = message.strip()
        if not message:
            continue

        x = MESSAGE_X
        base_y = MESSAGE_Y_INIT + i * MESSAGE_DY
        y_pos = base_y + y_offset
        current_x = x

        if is_emoji_message(message):
            with Pilmoji(template) as pilmoji:
                pilmoji.text((current_x, y_pos), message, MESSAGE_FONT_COLOR, font=message_font,
                             emoji_position_offset=(0, 8), emoji_scale_factor=2)
            y_offset += message_font.getbbox(message)[3]
            continue

        # Tokenize for bold (**), italic (__), strikethrough (~~), URLs, and mentions (@...)
        tokens = re.split(r'(\*\*|__|~~)', message)
        bold = italic = strike = False
        with Pilmoji(template) as pilmoji:
            for token in tokens:
                if token == '**':
                    bold = not bold
                elif token == '__':
                    italic = not italic
                elif token == '~~':
                    strike = not strike
                else:
                    if not token:
                        continue

                    parts = re.split(r'(?<!\S)(@\w+)', token)
                    for part in parts:
                        if not part:
                            continue
                        if part.startswith('@'):
                            if bold and italic:
                                font_used = message_mention_italic_font
                            elif bold:
                                font_used = message_mention_font
                            elif italic:
                                font_used = message_mention_italic_font
                            else:
                                font_used = message_mention_font

                            bbox = font_used.getbbox(part)
                            text_width = bbox[2] - bbox[0]
                            text_top = bbox[1]
                            text_bottom = bbox[3]
                            padding = 8
                            bg_box = [
                                current_x,
                                y_pos + text_top - padding,
                                current_x + text_width + 2 * padding,
                                y_pos + text_bottom + padding
                            ]
                            draw_template.rounded_rectangle(bg_box, fill=(74, 75, 114), radius=10)
                            pilmoji.text((current_x + padding, y_pos), part, (201, 205, 251), font=font_used)
                            if strike:
                                line_y = y_pos + (text_top + text_bottom) // 2
                                draw_template.line((current_x + padding, line_y,
                                                    current_x + padding + text_width, line_y),
                                                   fill=(201, 205, 251), width=max(1, MESSAGE_FONT_SIZE // 12))
                            current_x += text_width + 2 * padding
                        else:
                            sub_parts = re.split(URL_PATTERN, part)
                            for sub_part in sub_parts:
                                if not sub_part:
                                    continue
                                is_url = bool(URL_PATTERN.fullmatch(sub_part))
                                if bold and italic:
                                    font_used = message_italic_bold_font
                                elif bold:
                                    font_used = message_bold_font
                                elif italic:
                                    font_used = message_italic_font
                                else:
                                    font_used = message_font

                                part_color = (114, 137, 218) if is_url else MESSAGE_FONT_COLOR
                                width = _draw_text_part(
                                    draw_template,
                                    pilmoji,
                                    sub_part,
                                    font_used,
                                    current_x,
                                    y_pos,
                                    part_color,
                                    strike=strike,
                                    is_url=is_url
                                )
                                current_x += width
    return template


def generate_joined_message(name, time, template_str, arrow_x, color=NAME_FONT_COLOR):
    """
    Generates a Discord-like joined message with a green arrow.
    The character name will be colored with their role color.
    """
    before_text, after_text = template_str.split("CHARACTER", 1) if "CHARACTER" in template_str else ("", "")
    time_text = f'Today at {time} PM'
    
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, WORLD_HEIGHT_JOINED), color=WORLD_COLOR)
    draw_template = ImageDraw.Draw(template_img)
    
    arrow_path = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'green_arrow.png'))
    arrow = Image.open(arrow_path)
    arrow.thumbnail((40, 40))
    text_x = arrow_x + arrow.width + 60

    text_bbox = message_font.getbbox("Sample")
    text_height = text_bbox[3] - text_bbox[1]
    text_y = (WORLD_HEIGHT_JOINED - text_height) // 2
    message_ascent, message_descent = message_font.getmetrics()
    total_text_height = message_ascent + message_descent
    arrow_y = text_y + (total_text_height - arrow.height) // 2

    template_img.paste(arrow, (arrow_x, arrow_y), arrow)
    
    before_width = message_font.getbbox(before_text)[2] if before_text else 0
    name_width = name_font.getbbox(name)[2]
    with Pilmoji(template_img) as pilmoji:
        if before_text:
            pilmoji.text((text_x, text_y), before_text, JOINED_FONT_COLOR, font=message_font)
        name_x = text_x + before_width
        pilmoji.text((name_x, text_y), name, color, font=name_font)
        if after_text:
            after_x = name_x + name_width
            pilmoji.text((after_x, text_y), after_text, JOINED_FONT_COLOR, font=message_font)
        
        total_msg_width = before_width + name_width + message_font.getbbox(after_text)[2]
        time_x = text_x + total_msg_width + 30
        time_baseline = text_y + message_ascent
        time_y = time_baseline - time_font.getmetrics()[0]
        pilmoji.text((time_x, time_y), time_text, TIME_FONT_COLOR, font=time_font)
    
    return template_img


def generate_joined_message_stack(joined_messages, hour):
    """
    Generates a stacked image for multiple joined messages.
    """
    total_height = WORLD_HEIGHT_JOINED * len(joined_messages)
    template_img = Image.new(mode='RGBA', size=(WORLD_WIDTH, total_height), color=WORLD_COLOR)
    
    for idx, key in enumerate(joined_messages):
        name = key.split(' ')[1].split('$^')[0]
        color = characters_dict.get(name, DEFAULT_PROFILE)["role_color"]
        time_str = f'{hour}:{joined_messages[key][2].minute:02d}'
        joined_img = generate_joined_message(name, time_str, joined_messages[key][0], joined_messages[key][1], color)
        template_img.paste(joined_img, (0, idx * WORLD_HEIGHT_JOINED))
    
    return template_img


def get_filename():
    app = QApplication(sys.argv)
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(
        None, "Select Text File", "", "Text Files (*.txt);;All Files (*)", options=options
    )
    app.exit()
    return filename


def save_images(lines, init_time, dt=30):
    os.makedirs(CHAT_DIR, exist_ok=True)

    name_up_next = True
    current_time = init_time
    current_name = None
    current_lines = []
    msg_number = 1
    joined_messages = {}
    name_time = []

    # Parse script to extract per-message animations and durations
    try:
        parsed_events, _ = parse_script(lines)
        events_queue = [e for e in parsed_events if e['type'] in ('message', 'welcome', 'typing')]
    except Exception:
        events_queue = []

    for line in lines:
        line = line.strip()
        if not line:
            name_up_next = True
            current_lines = []
            name_time = []
            joined_messages = {}
            continue

        if line.startswith('#'):
            joined_messages = {}
            continue

        upper_line = line.upper()
        if upper_line.startswith('WELCOME '):
            joined_messages[line] = [random.choice(JOINED_TEXTS), random.randint(50, 80), current_time]
            hour = current_time.hour % 12 or 12
            image = generate_joined_message_stack(joined_messages, hour)
            image.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
            current_time += datetime.timedelta(seconds=dt)
            msg_number += 1
            continue

        if upper_line.startswith('TYPING '):
            typing_name = line[len('TYPING '):].split('$^', 1)[0].strip()
            if typing_name:
                current_name = typing_name
                current_lines = ['typing...']
                hour = current_time.hour % 12 or 12
                name_time = [current_name, f'{hour}:{current_time.minute:02d}']
                template_img = generate_chat(
                    messages=current_lines,
                    name_time=name_time,
                    profpic_file=os.path.join(PROFILE_PICS_DIR, characters_dict.get(current_name, DEFAULT_PROFILE)["profile_pic"]),
                    color=characters_dict.get(current_name, DEFAULT_PROFILE)["role_color"]
                )
                # handle animation if specified in parsed events
                anim = None
                if events_queue:
                    try:
                        ev = events_queue.pop(0)
                        anim = ev.get('animation')
                    except Exception:
                        anim = None

                if anim == 'fade-in':
                    frames = max(3, min(10, int(dt/0.2)))
                    blank = Image.new('RGBA', template_img.size, WORLD_COLOR)
                    for i in range(frames):
                        alpha = (i + 1) / frames
                        frame = Image.blend(blank, template_img, alpha)
                        frame.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
                        msg_number += 1
                elif anim and 'typewriter' in anim:
                    # reveal left-to-right
                    w = template_img.width
                    steps = max(4, min(12, int(dt/0.15)))
                    blank = Image.new('RGBA', template_img.size, WORLD_COLOR)
                    for i in range(steps):
                        reveal_w = int(w * (i + 1) / steps)
                        mask = Image.new('L', template_img.size, 0)
                        ImageDraw.Draw(mask).rectangle((0, 0, reveal_w, template_img.height), fill=255)
                        frame = Image.composite(template_img, blank, mask)
                        frame.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
                        msg_number += 1
                else:
                    template_img.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
                    msg_number += 1
                current_time += datetime.timedelta(seconds=dt)
            continue

        if re.match(r'^(?:BGM|MUSIC)\s*[:\s]+', line, re.IGNORECASE):
            continue

        if name_up_next:
            current_name = line.split(':')[0]
            hour = current_time.hour % 12 or 12
            name_time = [current_name, f'{hour}:{current_time.minute:02d}']
            name_up_next = False
            continue

        if '$^' not in line:
            continue

        message_text = line.split('$^', 1)[0].rstrip()
        current_lines.append(message_text)
        template_img = generate_chat(
            messages=current_lines,
            name_time=name_time,
            profpic_file=os.path.join(PROFILE_PICS_DIR, characters_dict.get(current_name, DEFAULT_PROFILE)["profile_pic"]),
            color=characters_dict.get(current_name, DEFAULT_PROFILE)["role_color"]
        )
        # handle animation if specified
        anim = None
        if events_queue:
            try:
                ev = events_queue.pop(0)
                anim = ev.get('animation')
            except Exception:
                anim = None

        if anim == 'fade-in':
            frames = max(3, min(10, int(dt/0.2)))
            blank = Image.new('RGBA', template_img.size, WORLD_COLOR)
            for i in range(frames):
                alpha = (i + 1) / frames
                frame = Image.blend(blank, template_img, alpha)
                frame.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
                msg_number += 1
        elif anim and 'typewriter' in anim:
            w = template_img.width
            steps = max(4, min(12, int(dt/0.15)))
            blank = Image.new('RGBA', template_img.size, WORLD_COLOR)
            for i in range(steps):
                reveal_w = int(w * (i + 1) / steps)
                mask = Image.new('L', template_img.size, 0)
                ImageDraw.Draw(mask).rectangle((0, 0, reveal_w, template_img.height), fill=255)
                frame = Image.composite(template_img, blank, mask)
                frame.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
                msg_number += 1
        else:
            template_img.save(os.path.join(CHAT_DIR, f'{msg_number:03d}.png'))
            msg_number += 1
        current_time += datetime.timedelta(seconds=dt)


if __name__ == '__main__':
    """
    final_video = '../final_video.mp4'
    if os.path.isfile(final_video):
        os.remove(final_video)
    if os.path.exists('../chat'):
        for file in os.listdir('../chat'):
            os.remove(os.path.join('../chat', file))
        os.rmdir('../chat')

    filename = get_filename()
    with open(filename, encoding="utf8") as f:
        lines = f.read().splitlines()

    current_time = datetime.datetime.now()
    save_images(lines, init_time=current_time)

    # The following function is imported from compile_images.py
    from compile_images import gen_vid
    gen_vid(filename)
    """
    
    print('Please run the main.py script!')