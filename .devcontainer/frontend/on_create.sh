source .devcontainer/bootstrap.sh

pip install -r dev/requirements.txt

sudo echo "cd /workspaces/taxos/frontend" >> ~/.bashrc
cd /workspaces/taxos/frontend
npm install