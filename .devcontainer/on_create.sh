sudo chown -R $USER /workspaces/taxos

pip install -r backend/requirements.txt
pip install -r dev/requirements.txt

git clone https://github.com/sycdan/dotfiles.git ~/dotfiles \
  && bash ~/dotfiles/install.sh

sudo echo "source .venvrc" >> ~/.bashrc
