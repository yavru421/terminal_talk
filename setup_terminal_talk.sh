#!/bin/bash
set -e

# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git

# 2. Clone the repo if not present
if [ ! -d terminal_talk ]; then
  git clone https://github.com/yavru421/terminal_talk.git
fi
cd terminal_talk

# 3. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# 5. Prompt for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
  read -p "Enter your GitHub token: " token
  export GITHUB_TOKEN="$token"
  echo "export GITHUB_TOKEN=$token" >> ~/.bashrc
fi

echo "Setup complete! You can now run: python asciichat_call.py"
