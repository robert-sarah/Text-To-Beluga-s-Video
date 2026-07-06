import os
from sound_effects import add_sounds

BASE_DIR = os.path.dirname(__file__)
CHAT_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'chat'))
OUTPUT_VIDEO = os.path.normpath(os.path.join(BASE_DIR, '..', 'output.mp4'))
FINAL_VIDEO_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'final_video.mp4'))
IMAGE_LIST_FILE = os.path.join(BASE_DIR, 'image_paths.txt')


def gen_vid(filename):
    input_folder = CHAT_DIR
    image_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])

    # Read durations from the file.
    durations = []
    with open(filename, encoding="utf8") as f:
        name_up_next = True
        
        lines = f.read().splitlines()
        for line in lines:
            if line == '':
                name_up_next = True
                continue
            elif line[0] == '#':
                continue
            elif line.startswith("WELCOME"):
                if "#!" in line:
                    durations.append(line.split('$^')[1].split("#!")[0])
                else:
                    durations.append(line.split('$^')[1])
                continue
            elif name_up_next == True:
                name_up_next = False
                continue
            else:
                if "#!" in line:
                    durations.append(line.split('$^')[1].split("#!")[0])
                else:
                    durations.append(line.split('$^')[1])
                
                
    # Create a text file to store the image paths
    with open(IMAGE_LIST_FILE, 'w') as file:    
        for count, image_file in enumerate(image_files):
            image_path = os.path.join(input_folder, image_file).replace('\\', '/')
            file.write(f"file '{image_path}'\noutpoint {durations[count]}\n")
        last_image_path = os.path.join(input_folder, image_files[-1]).replace('\\', '/')
        file.write(f"file '{last_image_path}'\noutpoint 0.04\n")

    video_width, video_height = 1280, 720
    # Build ffmpeg command and run it, checking for success
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i \"{IMAGE_LIST_FILE}\" -vcodec libx264 -r 25 -crf 25 "
        f"-vf \"scale={video_width}:{video_height}:force_original_aspect_ratio=decrease,"
        f"pad={video_width}:{video_height}:(ow-iw)/2:(oh-ih)/2\" -pix_fmt yuv420p \"{OUTPUT_VIDEO}\""
    )
    import subprocess
    proc = subprocess.run(ffmpeg_cmd, shell=True)
    # remove the temporary image list file
    try:
        os.remove(IMAGE_LIST_FILE)
    except Exception:
        pass

    # Only proceed to add sounds if ffmpeg produced the expected output file
    if not os.path.isfile(OUTPUT_VIDEO):
        print(f"Error: expected output video not found at {OUTPUT_VIDEO}. ffmpeg returncode={proc.returncode}")
        return

    add_sounds(filename, output_video=OUTPUT_VIDEO, final_video=FINAL_VIDEO_PATH)