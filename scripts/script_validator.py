import os
import sys
import re
import argparse
from PyQt5.QtWidgets import QApplication, QFileDialog

BASE_DIR = os.path.dirname(__file__)
SOUND_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'sounds', 'mp3'))
ANIMATION_TAGS = {'fade-in', 'fade_in', 'typewriter', 'typewriter-effect', 'shake', 'zoom-in', 'zoom_in', 'zoom', 'none'}


def get_filename():
    """Opens a file dialog and returns the selected filename."""
    app = QApplication(sys.argv)
    options = QFileDialog.Options()
    filename, _ = QFileDialog.getOpenFileName(
        None, "Select Script Text File", "", "Text Files (*.txt);;All Files (*)", options=options
    )
    app.exit()
    return filename


def _normalize_sound_name(sound_name):
    if not sound_name:
        return None
    sound_name = sound_name.strip()
    if sound_name.lower().endswith('.mp3'):
        return sound_name[:-4]
    return sound_name


def _sound_file_exists(sound_name):
    if not sound_name:
        return False
    sound_path = os.path.join(SOUND_DIR, f"{sound_name}.mp3")
    return os.path.isfile(sound_path)


def _parse_metadata(meta, line_num):
    if meta is None:
        return None, None, None, f"Line {line_num}: Missing duration metadata after '$^'."

    duration_meta = meta.strip()
    if duration_meta == '':
        return None, None, None, f"Line {line_num}: Missing duration metadata after '$^'."

    sound_name = None
    animation = None
    if '#!' in duration_meta:
        duration_part, tail = duration_meta.split('#!', 1)
        duration_part = duration_part.strip()
        tail = tail.strip()
        if '|' in tail:
            sound_part, animation_part = tail.split('|', 1)
            sound_name = _normalize_sound_name(sound_part)
            animation = animation_part.strip() or None
        else:
            sound_name = _normalize_sound_name(tail)
    elif '|' in duration_meta:
        duration_part, animation_part = duration_meta.split('|', 1)
        duration_part = duration_part.strip()
        animation = animation_part.strip() or None
    else:
        duration_part = duration_meta

    if animation and animation not in ANIMATION_TAGS:
        return None, None, None, f"Line {line_num}: Unknown animation tag '{animation}'. Supported effects: {', '.join(sorted(ANIMATION_TAGS))}."

    if duration_part == '':
        return None, None, None, f"Line {line_num}: Missing duration before metadata."

    try:
        duration = float(duration_part)
    except ValueError:
        return None, None, None, f"Line {line_num}: Unable to convert duration '{duration_part}' to a number."

    if sound_name and not _sound_file_exists(sound_name):
        if sound_name in ANIMATION_TAGS:
            animation = sound_name
            sound_name = None
        else:
            return None, None, None, f"Line {line_num}: Sound effect '{sound_name}' does not exist at expected location: {os.path.join(SOUND_DIR, sound_name + '.mp3')}"

    return duration, sound_name, animation, None


def _parse_action_line(line, action, line_num):
    if '$^' not in line:
        return None, f"Line {line_num}: Expected '$^' delimiter in {action.upper()} line but got: {line}"
    left, meta = line.split('$^', 1)
    name = left.strip()
    if not name:
        return None, f"Line {line_num}: {action.upper()} line must specify a character name before '$^'."

    duration, sound_name, animation, err = _parse_metadata(meta, line_num)
    if err:
        return None, err

    return {
        'type': action,
        'name': name,
        'duration': duration,
        'sound': sound_name,
        'animation': animation,
    }, None


def _parse_bgm_line(line, line_num):
    match = re.match(r'^(?:BGM|MUSIC)\s*[:\s]+(.+)$', line, re.IGNORECASE)
    if not match:
        return None, f"Line {line_num}: Expected BGM command in the form 'BGM: name' or 'MUSIC: name'."
    sound_name = _normalize_sound_name(match.group(1).strip())
    if not sound_name:
        return None, f"Line {line_num}: BGM command must include a music file name."
    if not _sound_file_exists(sound_name):
        return None, f"Line {line_num}: Background music '{sound_name}' does not exist at expected location: {os.path.join(SOUND_DIR, sound_name + '.mp3')}"
    return {'type': 'bgm', 'sound': sound_name}, None


def parse_script(lines):
    events = []
    errors = []
    current_name = None

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            if line == '':
                current_name = None
            continue

        upper = line.upper()
        if upper.startswith('WELCOME '):
            parsed, err = _parse_action_line(line[len('WELCOME '):], 'welcome', idx)
            if err:
                errors.append(err)
            else:
                events.append(parsed)
            current_name = None
            continue

        if upper.startswith('TYPING '):
            parsed, err = _parse_action_line(line[len('TYPING '):], 'typing', idx)
            if err:
                errors.append(err)
            else:
                events.append(parsed)
            current_name = None
            continue

        if re.match(r'^(?:BGM|MUSIC)\s*[:\s]+', line, re.IGNORECASE):
            parsed, err = _parse_bgm_line(line, idx)
            if err:
                errors.append(err)
            else:
                events.append(parsed)
            continue

        if line.endswith(':'):
            name = line[:-1].strip()
            if not name:
                errors.append(f"Line {idx}: Empty character name before ':'")
            else:
                current_name = name
            continue

        if current_name is None:
            errors.append(f"Line {idx}: Message line without a preceding character name: {line}")
            continue

        if '$^' not in line:
            errors.append(f"Line {idx}: Expected '$^' delimiter in message line but got: {line}")
            continue

        text, meta = line.split('$^', 1)
        message_text = text.rstrip()
        if not message_text:
            errors.append(f"Line {idx}: Message text cannot be empty before '$^'.")
            continue

        duration, sound_name, animation, err = _parse_metadata(meta, idx)
        if err:
            errors.append(err)
            continue

        events.append({
            'type': 'message',
            'name': current_name,
            'text': message_text,
            'duration': duration,
            'sound': sound_name,
            'animation': animation,
        })

    return events, errors


def validate_script_lines(lines):
    events, errors = parse_script(lines)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate a script text file for chat generation.")
    parser.add_argument("script_file", nargs="?", help="Path to the script text file. If not provided, a file dialog will open.")
    args = parser.parse_args()

    if args.script_file:
        filename = args.script_file
    else:
        filename = get_filename()

    if not filename or not os.path.isfile(filename):
        print("No valid file selected. Exiting.")
        sys.exit(1)

    with open(filename, encoding="utf8") as f:
        lines = f.read().splitlines()

    errors = validate_script_lines(lines)

    if errors:
        print("Script validation found issues:")
        for error in errors:
            print("  -", error)
    else:
        print("Script validation successful: no problems found.")

if __name__ == '__main__':
    # main()
    print('Please run the main.py script!')