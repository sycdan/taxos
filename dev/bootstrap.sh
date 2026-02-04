apt update

# Install networking & process management tools
apt install -y curl netcat-openbsd iputils-ping dnsutils procps

# Install grpcurl
curl -L https://github.com/fullstorydev/grpcurl/releases/download/v1.9.3/grpcurl_1.9.3_linux_x86_64.tar.gz -o /tmp/grpcurl.tar.gz && tar -xzf /tmp/grpcurl.tar.gz -C /tmp && mv /tmp/grpcurl /usr/local/bin/ && chmod +x /usr/local/bin/grpcurl && rm /tmp/grpcurl.tar.gz

pip install -r dev/requirements.txt

echo "eval \"$(scaf)\"" > /root/.bashrc
echo "eval \"$(scaf .)\"" > /root/.bashrc
echo "alias | grep scaf" > /root/.bashrc
