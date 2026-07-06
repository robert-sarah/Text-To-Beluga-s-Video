# DONE
- fix only emojis message template
- fix timestamp not incrementing in joined messages
- fix timestamp on message incrementing when not needed
- optimize code
- make a script validator
- good cmd-line user interface
- write a README file

----------------------------------------------------

# (TRY) TODO
- AI powered chat script creator
- Text2Beluga discord bot

----------------------------------------------------

# IN PROGRESS
- Effects/animations: experimental support added for `fade-in` and `typewriter` (more to come)

----------------------------------------------------

# DONE (RECENT)
- allow for strikethrough message text
- ability to add background music
- support for links (URLs)
- improve script_validator.py
- "User is typing..." indicator

----------------------------------------------------

# NOTES
- The generator writes intermediate PNG frames to the `chat/` directory and produces a temporary `output.mp4` with ffmpeg. The final output is `final_video.mp4` in the repository root.
- Animations are implemented by producing multiple frames per message; this increases output size but is simple and cross-platform. Consider moving heavy effects into ffmpeg filters later.