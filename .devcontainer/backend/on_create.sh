source .devcontainer/bootstrap.sh

pip install -r backend/requirements.txt
pip install -r dev/requirements.txt

sudo echo "source .venvrc" >> ~/.bashrc