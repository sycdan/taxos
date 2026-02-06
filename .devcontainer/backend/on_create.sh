source .devcontainer/bootstrap.sh

pip install -r backend/requirements.txt
pip install -r dev/requirements.txt

sudo echo "eval \"$(scaf)\"" >> ~/.bashrc
sudo echo "eval \"$(scaf .)\"" >> ~/.bashrc
sudo echo "alias | grep scaf" >> ~/.bashrc
