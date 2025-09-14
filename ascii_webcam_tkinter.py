from PIL import Image, ImageDraw, ImageFont, ImageTk
import glob

import os
import time
import cv2
import numpy as np
import tkinter as tk
import sounddevice as sd
import soundfile as sf

ASCII_CHARS = "@$B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/|()1{}[]?-_+~<>i!lI;:,^`'. "

# Convert frame to ASCII grid with color

def frame_to_ascii_grid(frame, width=120):
    h, w, _ = frame.shape
    aspect = h / w
    new_w = width
    new_h = int(aspect * new_w * 0.6)
    block_w = w / new_w
    block_h = h / new_h
    grid = []
    for y in range(new_h):
        row = []
        for x in range(new_w):
            x1 = int(x * block_w)
            x2 = int((x + 1) * block_w)
            y1 = int(y * block_h)
            y2 = int((y + 1) * block_h)
            block = frame[y1:y2, x1:x2]
            if block.size == 0:
                b = g = r = 0
                brightness = 0
            else:
                b = int(np.mean(block[:, :, 0]))
                g = int(np.mean(block[:, :, 1]))
                r = int(np.mean(block[:, :, 2]))
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
            char = ASCII_CHARS[int((brightness / 255) * (len(ASCII_CHARS) - 1))]
            row.append((char, r, g, b))
        grid.append(row)
    return grid

def record_webcam(seconds=5, width=120):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None, 0, None, 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    frames = []
    audio_sr = 44100
    audio = []
    start = time.time()
    audio_recording = []
    def audio_callback(indata, frames, time_info, status):
        audio_recording.append(indata.copy())
    with sd.InputStream(samplerate=audio_sr, channels=1, callback=audio_callback):
        while time.time() - start < seconds:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame.copy())
            cv2.imshow('Recording...', cv2.resize(frame, (320, 240)))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()
    audio = np.concatenate(audio_recording, axis=0)
    return frames, fps, audio, audio_sr

def play_ascii_tkinter(ascii_grids, fps=15, font_size=10, font_family="Consolas"):
    if not ascii_grids:
        def dummy_play(audio, audio_sr):
            pass
        return dummy_play
    rows = len(ascii_grids[0])
    cols = len(ascii_grids[0][0])
    char_w = font_size
    char_h = int(font_size * 1.2)
    width = cols * char_w
    height = rows * char_h
    root = tk.Tk()
    root.title("ASCII Video Player (Tkinter)")
    canvas = tk.Canvas(root, width=width, height=height, bg="black", highlightthickness=0)
    canvas.pack()
    # Use a monospace font from PIL
    try:
        pil_font = ImageFont.truetype("Consola.ttf", font_size)
    except Exception:
        pil_font = ImageFont.load_default()

    tk_img = None

    def grid_to_tkimg(grid):
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        for y, row in enumerate(grid):
            for x, (char, r, g, b) in enumerate(row):
                r = int(r)
                g = int(g)
                b = int(b)
                draw.text((x * char_w, y * char_h), char, font=pil_font, fill=(r, g, b))
        return ImageTk.PhotoImage(img)

    # Pre-render all frames to images
    print("[DEBUG] Pre-rendering all frames to images...")
    tk_imgs = [grid_to_tkimg(grid) for grid in ascii_grids]
    print(f"[DEBUG] Pre-rendered {len(tk_imgs)} frames.")

    def draw_frame_idx(idx):
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=tk_imgs[idx])
        root.update()

    # Real-time playback using actual frame timestamps
    import threading
    def play_video_with_audio(audio, audio_sr):
        # Set FPS so playback always lasts exactly 5 seconds
        n_frames = len(ascii_grids)
        playback_duration = 5.0
        fps_sync = n_frames / playback_duration if playback_duration > 0 else 30
        print(f"[DEBUG] FPS for 5s playback: {fps_sync}")
        # Start audio playback first
        if audio is not None:
            sd.play(audio, audio_sr)
        t0 = time.time()
        for i in range(len(tk_imgs)):
            try:
                draw_frame_idx(i)
            except RuntimeError:
                print("[INFO] Tkinter window closed. Stopping playback.")
                break
            t_target = t0 + (i + 1) / fps_sync
            t_now = time.time()
            delay = t_target - t_now
            if delay > 0:
                time.sleep(delay)
        if audio is not None:
            sd.wait()  # Wait for audio to finish
        root.mainloop()
    return play_video_with_audio

def main():
    mode = input("Type 'r' to record new, or 'p' to replay last: ").strip().lower()
    if mode == 'p':
        # Replay mode: load ascii frames and audio
        print("Replaying last saved ASCII video and audio...")
        try:
            audio, audio_sr = sf.read("ascii_audio.wav")
            print(f"[DEBUG] Loaded audio: shape={audio.shape}, sr={audio_sr}")
        except Exception as e:
            print(f"[ERROR] Could not load ascii_audio.wav: {e}")
            return
        try:
            with open("last_ascii_frames.npz", "rb") as f:
                npz = np.load(f, allow_pickle=True)
                ascii_grids = npz['ascii_grids'].tolist()
                fps = int(npz['fps'])
            print(f"[DEBUG] Loaded ascii_grids: {len(ascii_grids)} frames, fps={fps}")
        except Exception as e:
            print(f"[ERROR] Could not load last_ascii_frames.npz: {e}")
            print("No previous ASCII frames found. Please record first.")
            return
        play_video_with_audio = play_ascii_tkinter(ascii_grids, 60, font_size=10, font_family="Consolas")
        if callable(play_video_with_audio):
            play_video_with_audio(audio, audio_sr)
    else:
        print("Recording webcam and audio for 5 seconds...")
        frames, fps, audio, audio_sr = record_webcam(5, 120)
        if not frames:
            print("Webcam not found!")
            return
        print(f"Converting {len(frames)} frames to ASCII...")
        ascii_grids = [frame_to_ascii_grid(f, 120) for f in frames]
        print("Saving audio to ascii_audio.wav...")
        sf.write("ascii_audio.wav", audio, audio_sr)
        # Save ASCII frames and fps for replay
        np.savez_compressed("last_ascii_frames.npz", ascii_grids=ascii_grids, fps=fps)
        print("Playing back in Tkinter window with audio...")
        play_video_with_audio = play_ascii_tkinter(ascii_grids, int(fps), font_size=10, font_family="Consolas")
        if callable(play_video_with_audio):
            play_video_with_audio(audio, audio_sr)

if __name__ == "__main__":
    main()
