import os
import subprocess
import argparse
import shlex

def convert(
        hwaccel: str, 
        hwaccel_format: None | str, 
        ac: str, 
        ab: str, 
        ar: str, 
        al: str, 
        vc: str, 
        vb: str, 
        crf: None | str, 
        p: str, 
        s: list, 
        pfmt: str, 
        fg: int,
        loglevel: str, 
        passthrough: list, 
        out_freq: str,
):
    if crf:
        video_quality_args = ['-cq', crf] if any(enc in vc for enc in ('nvenc', 'qsv', 'amf')) else ['-crf', crf]
    else:
        video_quality_args = ['-b:v', vb]
    hardware_accel_format = ['-hwaccel_output_format', hwaccel_format] if hwaccel_format else []
    hardware_accel_format = ['-hwaccel_output_format', hwaccel_format] if hwaccel_format else []
    pix_fmt_args = [] if hwaccel_format else ['-pix_fmt', pfmt]

    for file in os.listdir("input"):
        if not (file.endswith(".mp4") or file.endswith(".mkv")):
            continue
    
        print(f"Converting {file}...")
        output = file.replace(" ", "_").replace(".mp4", ".mkv")

        rife = None
        process = None
        if fg == 1:
            subs_map = [item for sub in s for item in ("-map", f"0:s:m:language:{sub}")]
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-hwaccel', hwaccel,    # Hardware acceleration
                *hardware_accel_format, # Hardware acceleration format
                '-i', f'input/{file}',
                '-vcodec', vc,          # Video codec
                *video_quality_args,    # Video quality, bitrate or crf
                *pix_fmt_args,          # Pixel format
                '-preset', p,           # Codec Preset
                '-acodec', ac,          # Audio codec
                '-b:a', ab,             # Audio bitrate
                '-ar', ar,              # Audio sample rate
                '-af', 'aresample=async=1:first_pts=0', # Audio timestamps
                '-frame_duration', '20', # Audio frame duration
                '-scodec', 'ass',       # Subtitles codec
                '-map', '0:v:0',        # Video mapping
                '-map', f'0:a:m:language:{al}', # Audio mapping, single audio only
                *s,                     # Subtitles
                "-disposition:s:0", "default",
                '-map_metadata', '-1',  # Overwrite metadata
                '-v', loglevel,         # Verbosity
                '-stats',               # Progress bar
                '-stats_period', f'{out_freq}.0',   # Progress bar refresh rate
                *passthrough,           # Pass arguments to ffmpeg
                f'output/{output}'
            ]

            print("CMD:", cmd)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        elif fg > 1:
            subs_map = [item for sub in s for item in ("-map", f"1:s:m:language:{sub}")]
            cmd1 = [
                "vspipe",
                "-c", "y4m",
                "interpolate.py",
                "-a", f"input=input/{file}",
                "-a", f"factor={fg}",
                "-"
            ]
            cmd = [
                'ffmpeg',
                '-hide_banner',
                # '-hwaccel', hwaccel,    # Hardware acceleration
                # *hardware_accel_format, # Hardware acceleration format
                '-i', 'pipe:',          # Input 0: Video stream with fg
                '-i', f'input/{file}',  # Input 1: Original file
                '-vcodec', vc,          # Video codec
                *video_quality_args,    # Video quality, bitrate or crf
                *pix_fmt_args,          # Pixel format
                '-preset', p,           # Codec preset
                '-acodec', ac,          # Audio codec
                '-b:a', ab,             # Audio bitrate
                '-ar', ar,              # Audio sample rate
                '-af', 'aresample=async=1:first_pts=0', # Audio timestamps
                '-frame_duration', '20', # Audio frame duration
                '-scodec', 'ass',       # Subtitles codec
                '-map', '0:v:0',        # Video mapping
                '-map', f'1:a:m:language:{al}', # Audio mapping, single audio only
                *subs_map,              # Subtitles
                "-disposition:s:0", "default",
                '-map_metadata', '-1',  # Overwrite metadata
                '-v', loglevel,         # Verbosity
                '-stats',               # Progress bar
                '-stats_period', f'{out_freq}.0',   # Progress bar refresh rate
                *passthrough,           # Pass arguments to ffmpeg
                f'output/{output}'
            ]
            rife = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
            process = subprocess.Popen(cmd, stdin=rife.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            rife.stdout.close()

        log_file = open(f"output/{output}.log", "w")
        log_file.write(f"CMD: {cmd}")
        while True:
            chunk = process.stdout.read(1).decode('utf-8', errors='replace')
            if not chunk and process.poll() is not None:
                break
            
            if chunk:
                print(chunk, end='', flush=True)
                log_file.write(chunk)
        log_file.close()

        if rife is not None:
            rife.kill()
        if process is not None:
            process.kill()

        if process.returncode != 0:
            raise RuntimeError(f"\nProcess finished with exit code: {process.returncode}")
        print(f"Converted {file} to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Converter", description="Simple tool for transcoding. Use @args.txt to pass arguments in a file.", fromfile_prefix_chars='@')
    parser.add_argument("-vc", "--video_codec", help="Set the video codec (default: libstvav1)", type=str, default="libsvtav1")
    parser.add_argument("-vb", "--video_bitrate", help="Set the video bitrate (default: 3000k)", type=str, default="3000k")
    parser.add_argument("-crf", "-cq", help="Set the video Constant Rate Factor / Constant Quality (0-51). Overrides bitrate if set. (default: not set)", type=str, default=None)
    parser.add_argument("-p", "--preset", help="Set the encoder preset (default: 4)", type=str, default="4")
    parser.add_argument("-pfmt", "--pixel_format", help="Set the pixel format (default: yuv420p10le)", type=str, default="yuv420p10le")
    parser.add_argument("-ac", "--audio_codec", help="Set the audio codec (default: libopus)", type=str, default="libopus")
    parser.add_argument("-ab", "--audio_bitrate", help="Set the audio bitrate (default: 96k)", type=str, default="96k")
    parser.add_argument("-ar", "--audio_samplerate", help="Set the audio sample rate in Hz (default: 48000)", type=str, default="48000")
    parser.add_argument("-al", "--audio_lang", help="Set the audio language, takes from source (default: jpn)", type=str, default="jpn")
    parser.add_argument("-hwaccel", "--hardware_acceleration", help="Set the hardware acceleration device (default: auto)", type=str, default="auto")
    parser.add_argument("--hwaccel_output_format", help="Set the hardware acceleration output format. Overrides pixel format if set (default: not set)", type=str, default=None)
    parser.add_argument("-s", "--subtitles", help="Set the subtitles languages, can set multiple languages, takes from source (default: fre)", nargs='+', default=["fre",])
    parser.add_argument("-pass", "--passthrough", help="Pass the argument to ffmpeg", type=str, default=None)
    parser.add_argument("-v", "--loglevel", help="Set the loglevel of ffmpeg (default: warning)", type=str, default="warning")
    parser.add_argument("--out_freq", help="Set the stats output refresh frequency for the progress bar, in seconds (default: 10)", type=str, default="10")

    parser.add_argument("-fg", "--frame_gen", help="Set the frame interpolation factor using RIFE. Disables hwaccel options (default: 1 (no gen))", type=int, default=1)

    parser.add_argument("--sleep", help="Sleep after finished", type=bool, default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--shutdown", help="Shutdown after finished", type=bool, default=False, action=argparse.BooleanOptionalAction)

    parser.add_argument("-ds", help="3ds params", type=bool, default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.ds:
        args.audio_codec = 'aac'
        args.audio_bitrate = '96k'
        args.audio_samplerate = '36000'
        args.video_codec = 'mpeg4'
        args.video_bitrate = '600k'
        args.resolution = '400x240'
        args.pixel_format = 'yuv420p'

    if args.frame_gen <= 0:
        raise RuntimeError("--frame_gen must be positive")

    if not os.path.isdir("input"):
        os.mkdir("input")
    if not os.path.isdir("output"):
        os.mkdir("output")

    input("Put your .mp4/.mkv files in the input folder and press enter to continue...")

    convert(
        args.hardware_acceleration,
        args.hwaccel_output_format,
        args.audio_codec,
        args.audio_bitrate,
        args.audio_samplerate,
        args.audio_lang,
        args.video_codec,
        args.video_bitrate,
        args.crf,
        args.preset,
        args.subtitles,
        args.pixel_format,
        args.frame_gen,
        args.loglevel,
        shlex.split(args.passthrough) if args.passthrough else [],
        args.out_freq
    )

    match os.name:
        case 'nt':
            if args.shutdown:
                os.system("shutdown /s /t 10")
            elif args.sleep:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        case 'posix':
            if args.shutdown:
                os.system("shutdown")
            elif args.sleep:
                os.system("systemctl suspend")
