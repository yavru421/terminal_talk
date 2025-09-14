import os
from asciichat_config import load_or_create_config
from asciichat_directory import register_handle, lookup_handle

def main_menu():
    print("\n=== ASCII Terminal Video Chat ===")
    print("1. Register/Update my handle")
    print("2. Lookup peer handle")
    print("3. Add/Update any peer handle")
    print("4. Exit")
    choice = input("Select an option: ").strip()
    return choice

def main():
    config = load_or_create_config()
    while True:
        choice = main_menu()
        if choice == "1":
            my_address = input("Enter your Tailscale IP or address: ").strip()
            register_handle(config["handle"], my_address)
            print(f"[INFO] Registered {config['handle']} -> {my_address}")
        elif choice == "2":
            peer = input("Enter peer handle to look up: ").strip()
            addr = lookup_handle(peer)
            if addr:
                print(f"[INFO] Peer {peer} address: {addr}")
            else:
                print(f"[WARN] Peer {peer} not found in directory.")
        elif choice == "3":
            peer_handle = input("Enter peer handle to add/update: ").strip()
            peer_address = input("Enter peer's Tailscale IP or address: ").strip()
            register_handle(peer_handle, peer_address)
            print(f"[INFO] Registered {peer_handle} -> {peer_address}")
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
