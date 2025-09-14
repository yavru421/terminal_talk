import os
import socket
import threading
import time
from asciichat_config import load_or_create_config
from asciichat_directory import lookup_handle
from ascii_webcam_tkinter import record_webcam, frame_to_ascii_grid, play_ascii_tkinter
import numpy as np
import io

PORT = 50007

# --- Ring/Accept/Reject Protocol ---
def ring_peer(peer_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        try:
            s.connect((peer_ip, PORT))
            s.sendall(b'RING')
            resp = s.recv(16)
            if resp == b'ACCEPT':
                print("[INFO] Call accepted! Sending video/audio...")
                return True
            else:
                print("[INFO] Call rejected or no response.")
                return False
        except Exception as e:
            print(f"[ERROR] Could not connect to peer: {e}")
            return False

def wait_for_ring():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', PORT))
        s.listen(1)
        print(f"[INFO] Waiting for incoming call on port {PORT}...")
        conn, addr = s.accept()
        with conn:
            print(f"[INFO] Incoming call from {addr[0]}")
            msg = conn.recv(16)
            if msg == b'RING':
                ans = input("Accept call? (y/n): ").strip().lower()
                if ans == 'y':
                    conn.sendall(b'ACCEPT')
                    return True, addr[0]
                else:
                    conn.sendall(b'REJECT')
                    return False, None
            else:
                print("[WARN] Unknown message received.")
                return False, None

# --- Video/Audio Send/Receive ---
def send_video_audio(peer_ip):
    frames, fps, audio, audio_sr = record_webcam(5, 120)
    if not frames or audio is None:
        print("Webcam or audio not found! Aborting.")
        return
    ascii_grids = [frame_to_ascii_grid(f, 120) for f in frames]
    buf = io.BytesIO()
    np.savez_compressed(buf, ascii_grids=ascii_grids, audio=audio, audio_sr=audio_sr)
    data = buf.getvalue()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((peer_ip, PORT))
        s.sendall(len(data).to_bytes(8, 'big'))
        s.sendall(data)
    print("[INFO] Sent ASCII video/audio to peer!")

def receive_video_audio():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', PORT))
        s.listen(1)
        print(f"[INFO] Waiting for video data on port {PORT}...")
        conn, addr = s.accept()
        with conn:
            print(f"[INFO] Receiving video data from {addr[0]}")
            size_bytes = b''
            while len(size_bytes) < 8:
                chunk = conn.recv(8 - len(size_bytes))
                if not chunk:
                    print("[ERROR] Connection closed while receiving size")
                    return
                size_bytes += chunk
            total_size = int.from_bytes(size_bytes, 'big')
            print(f"[INFO] Expecting {total_size} bytes...")
            data = b''
            while len(data) < total_size:
                chunk = conn.recv(min(4096, total_size - len(data)))
                if not chunk:
                    print("[ERROR] Connection closed while receiving data")
                    return
                data += chunk
            print(f"[INFO] Received {len(data)} bytes.")
            npz = np.load(io.BytesIO(data), allow_pickle=True)
            ascii_grids = npz['ascii_grids'].tolist()
            audio = npz['audio']
            audio_sr = int(npz['audio_sr'])
            print(f"[INFO] Playing back {len(ascii_grids)} frames, audio_sr={audio_sr}")
            play_video_with_audio = play_ascii_tkinter(ascii_grids, 30, font_size=10, font_family="Consolas")
            if callable(play_video_with_audio):
                play_video_with_audio(audio, audio_sr)

# --- Unified CLI ---
def main():
    config = load_or_create_config()
    print("\n=== ASCII Terminal Video Chat (Call) ===")
    print("1. Wait for call (receiver)")
    print("2. Call a peer (sender)")
    print("3. Exit")
    choice = input("Select an option: ").strip()
    if choice == "1":
        accepted, peer_ip = wait_for_ring()
        if accepted:
            print("[INFO] Call accepted. Waiting for video data...")
            receive_video_audio()
    elif choice == "2":
        peer_handle = input("Enter peer handle: ").strip()
        peer_ip = lookup_handle(peer_handle)
        if not peer_ip:
            print(f"[WARN] Peer {peer_handle} not found in directory.")
            return
        if ring_peer(peer_ip):
            time.sleep(2)  # Give peer time to get ready for video data
            send_video_audio(peer_ip)
    else:
        print("Goodbye!")

if __name__ == "__main__":
    main()
