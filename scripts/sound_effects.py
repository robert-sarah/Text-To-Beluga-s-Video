import os
import re
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

SOUND_DIR = os.path.join('..', 'assets', 'sounds', 'mp3')

BASE_DIR = os.path.dirname(__file__)
SOUND_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'assets', 'sounds', 'mp3'))


def _normalize_sound_name(sound_name):
    if not sound_name:
        return None
    sound_name = sound_name.strip()
    if sound_name.lower().endswith('.mp3'):
        return sound_name[:-4]
    return sound_name


def _parse_sound_meta(meta):
    if not meta:
        return None
    if '#!' not in meta:
        return None
    raw_tail = meta.split('#!', 1)[1].strip()
    if '|' in raw_tail:
        sound_part = raw_tail.split('|', 1)[0].strip()
    else:
        sound_part = raw_tail
    return _normalize_sound_name(sound_part)


def _sound_path(sound_name):
    return os.path.join(SOUND_DIR, f"{sound_name}.mp3")


def add_sounds(filename, output_video=None, final_video=None):
    if output_video is None:
        output_video = os.path.normpath(os.path.join(BASE_DIR, '..', 'output.mp4'))
    if final_video is None:
        final_video = os.path.normpath(os.path.join(BASE_DIR, '..', 'final_video.mp4'))
    video = VideoFileClip(output_video)
    video_duration = video.duration
    audio_clips = []
    bgm_clip = None
    current_time = 0.0
    name_up_next = True

    with open(filename, encoding="utf8") as f:
        for line in f.read().splitlines():
            raw_line = line.strip()
            if not raw_line or raw_line.startswith('#'):
                if raw_line == '':
                    name_up_next = True
                continue

            upper_line = raw_line.upper()
            if re.match(r'^(?:BGM|MUSIC)\s*[:\s]+', raw_line, re.IGNORECASE):
                sound_name = _normalize_sound_name(re.split(r'^(?:BGM|MUSIC)\s*[:\s]+', raw_line, flags=re.IGNORECASE)[1])
                if sound_name:
                    path = _sound_path(sound_name)
                    if os.path.isfile(path):
                        bgm = AudioFileClip(path)
                        bgm_clip = bgm.subclip(0, min(video_duration, bgm.duration)).volumex(0.65)
                continue

            if upper_line.startswith('WELCOME '):
                duration_meta = raw_line.split('$^', 1)[1]
                sound_name = _parse_sound_meta(duration_meta)
                if sound_name:
                    path = _sound_path(sound_name)
                    if os.path.isfile(path):
                        audio_clips.append(AudioFileClip(path).set_start(current_time))
                current_time += float(duration_meta.split('#!')[0].strip())
                name_up_next = True
                continue

            if upper_line.startswith('TYPING '):
                duration_meta = raw_line.split('$^', 1)[1] if '$^' in raw_line else '1'
                sound_name = _parse_sound_meta(duration_meta)
                if sound_name:
                    path = _sound_path(sound_name)
                    if os.path.isfile(path):
                        audio_clips.append(AudioFileClip(path).set_start(current_time))
                current_time += float(duration_meta.split('#!')[0].strip())
                name_up_next = True
                continue

            if name_up_next:
                name_up_next = False
                continue

            if '$^' not in raw_line:
                continue

            duration_meta = raw_line.split('$^', 1)[1]
            sound_name = _parse_sound_meta(duration_meta)
            if sound_name:
                path = _sound_path(sound_name)
                if os.path.isfile(path):
                    audio_clips.append(AudioFileClip(path).set_start(current_time))
            current_time += float(duration_meta.split('#!')[0].strip())

    if bgm_clip is not None:
        audio_clips.append(bgm_clip)

    if audio_clips:
        composite_audio = CompositeAudioClip(audio_clips)
        video = video.set_audio(composite_audio)

    video.write_videofile(final_video, codec="libx264", audio_codec="aac")
    # remove the intermediate output file created by ffmpeg (output_video path passed from caller)
    try:
        if os.path.isfile(output_video):
            os.remove(output_video)
    except Exception:
        # best-effort cleanup; ignore failures
        pass