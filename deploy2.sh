#!/bin/bash

# Define variables
REPO_URL="https://github.com/xbaloyi/asst-cam-software-test.git"
REPO_DIR="$HOME/svn-test/asst-cam-software-test"
LOG_FILE="$HOME/deploy.log"
VENV_DIR="$REPO_DIR/venv"
IMAGE_NAME="astt-cam-software"

# Function to print messages in color
print_msg() {
  local color="$1"
  shift
  echo -e "$(tput setaf $color)$@$(tput sgr0)"
}

# Create the repository directory if it doesn't exist
if [ ! -d "$HOME/svn-test" ]; then
  print_msg 2 "Creating $HOME/svn-test directory."
  mkdir -p "$HOME/svn-test"
fi

# Create or switch to the repository directory
if [ -d "$REPO_DIR" ]; then
  print_msg 2 "Repository directory exists. Changing to it..."
  cd "$REPO_DIR"
else
  print_msg 2 "Cloning the repository..."
  git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_FILE" 2>&1
  cd "$REPO_DIR"
fi

# Pull the latest changes if the repository exists
if [ -d ".git" ]; then
  print_msg 2 "Pulling the latest changes..."
  git pull >> "$LOG_FILE" 2>&1
  sleep 5
fi

# Set up Python virtual environment in the repository directory
if [ ! -d "$VENV_DIR" ]; then
  print_msg 2 "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
  sleep 3
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_msg 2 "Upgrading pip..."
pip install --upgrade pip >> "$LOG_FILE" 2>&1
sleep 2

# Install Poetry if not already installed
if ! command -v poetry &> /dev/null; then
  print_msg 2 "Installing Poetry..."
  pip install poetry >> "$LOG_FILE" 2>&1
  sleep 2
fi

# Install dependencies
print_msg 2 "Installing dependencies..."
poetry config virtualenvs.create false >> "$LOG_FILE" 2>&1
poetry install >> "$LOG_FILE" 2>&1
sleep 5

# Check if Docker image exists, and skip build if it does
if docker image inspect "$IMAGE_NAME" &> /dev/null; then
  print_msg 2 "Docker image $IMAGE_NAME already exists. Skipping build."
else
  print_msg 2 "Building Docker image..."
  docker build -t "$IMAGE_NAME" . >> "$LOG_FILE" 2>&1
  sleep 15
fi

# Check for existing Docker containers using the image
container_ids=$(docker ps -q --filter "ancestor=$IMAGE_NAME")

if [ -n "$container_ids" ]; then
  print_msg 2 "Stopping and removing existing Docker containers..."
  docker stop $container_ids >> "$LOG_FILE" 2>&1
  docker rm $container_ids >> "$LOG_FILE" 2>&1
else
  print_msg 2 "No running containers using image '$IMAGE_NAME' found."
fi

# Run Flask app in the background
print_msg 2 "Running Flask app..."
nohup gunicorn -w 1 src.astt_gui.app:app -b 0.0.0.0:5000 >> "$LOG_FILE" 2>&1 &
sleep 3

print_msg 2 "Deployment complete."
