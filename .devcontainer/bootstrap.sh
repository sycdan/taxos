mkdir -p ~/.local/bin
sudo chown -R $USER /workspaces/taxos
sudo apt-get update

# Install Buf
curl -sSL \
  "https://github.com/bufbuild/buf/releases/download/v1.34.0/buf-Linux-x86_64" \
  -o ~/.local/bin/buf \
  && chmod +x ~/.local/bin/buf

# Install grpcurl
curl -sSL \
  https://github.com/fullstorydev/grpcurl/releases/download/v1.9.1/grpcurl_1.9.1_linux_x86_64.tar.gz \
  | tar -xz -C ~/.local/bin \
  && chmod +x ~/.local/bin/grpcurl

git clone https://github.com/sycdan/dotfiles.git ~/dotfiles
bash ~/dotfiles/install.sh
