sudo chown -R $USER /workspaces/taxos

pip install -r backend/requirements.txt
pip install -r dev/requirements.txt

# Make scaf aliases available
sudo echo "source .venvrc" >> ~/.bashrc

git clone https://github.com/sycdan/dotfiles.git ~/dotfiles \
  && bash ~/dotfiles/install.sh

