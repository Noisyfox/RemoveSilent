# RemoveSilent
A simple script to delete all silent videos

# Howto
1. Create a virtualenv in ./venv/
2. Enter that virtual environment, run
`pip install -r requirements.txt`
3. (Optional) Install ffmpeg or libav according to [here](https://github.com/jiaaro/pydub#getting-ffmpeg-set-up).
4. Run `remove_silent.bat <video_dir>` or drag the folder onto _remove_silent.bat_.
5. Use `remove_silent.bat -d <video_dir>` to perform a dry run which will list all silent video files without deleting them.
