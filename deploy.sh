  GNU nano 6.2                                  deploy.sh                                            
#!/bin/bash
set -e

REPO_DIR="$HOME/svn-tes/asst-cam-software-test"
IMAGE_NAME="astt-cam-software"
GIT_REPO="https://github.com/xbaloyi/asst-cam-software-test.git"

# Ensure the /svn directory exists
if [ ! -d "$HOME/svn-tes" ]; then
  echo "Creating $HOME/svn directory."
  mkdir -p $HOME/svn-tes
 #sudo chown -R $asst:$asst $HOME/svn-tes
 #sudo chmod -R 755 $HOME/svn-tes
fi

# Check if the repository exists
if [ -d "$REPO_DIR" ]; then
  echo "Repository exists. Pulling latest changes."
  cd $REPO_DIR
  git pull
else
  echo "Repository does not exist. Cloning repository."
  git clone $GIT_REPO $REPO_DIR
  cd $REPO_DIR
fi

# Check if Docker image exists
if docker images -q $IMAGE_NAME:latest > /dev/null; then
  echo "Docker image exists."
else
  echo "Docker image does not exist. Building Docker image."
  docker build -t $IMAGE_NAME .
fi

# Install Poetry and dependencies
pip install poetry
poetry config virtualenvs.create false
poetry install

# Start the Flask application
echo "Starting Flask application."
gunicorn -b 0.0.0.0:5000 src.swet_gui.app:app &

echo "Deployment complete."
