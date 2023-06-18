# Minecraft Server

Amazon Linux 2023 (>=t4g.small):

```sh
# パッケージをインストール
sudo dnf update -y
sudo dnf install java-17-amazon-corretto-devel -y

# タイムゾーンを設定
sudo timedatectl set-timezone Asia/Tokyo

# ゲームディレクトリを作成
mkdir $HOME/minecraft
cd $HOME/minecraft

# サーバーをダウンロード
curl -o paper.jar https://api.papermc.io/v2/projects/paper/versions/1.20/builds/8/downloads/paper-1.20-8.jar

# 初回起動
java -jar paper.jar  # すぐに停止し、規約への同意を要求される

# 規約に同意
sed -i s/^eula=false$/eula=true/g eula.txt

# RCON を有効化
read -sp "rcon.password: " rcon_password; echo  # パスワードを設定

sed -i \
    -e "s/^rcon.password=$/rcon.password=$rcon_password/g" \
    -e s/^enable-rcon=false$/enable-rcon=true/g \
    server.properties
```

test run:

```sh
java -Xmx2G -jar paper.jar
```

serve:

```sh
sudo bash -c "cat << EOF > /etc/systemd/system/minecraft.service
[Unit]
Description=Minecraft Server

[Service]
WorkingDirectory=$HOME/minecraft
ExecStart=`which java` -Xmx2G -jar $HOME/minecraft/paper.jar
Restart=always
Type=simple
User=`whoami`

[Install]
WantedBy=multi-user.target
EOF"
sudo systemctl daemon-reload
sudo systemctl enable minecraft.service
sudo systemctl restart minecraft.service
```

## Operations

In the case of introducing additional autonomous operation scripts for server maintenance:

```sh
sudo dnf install git -y
python3 -m venv $HOME/venv
$HOME/venv/bin/python -m pip install "mcops @ git+https://github.com/oshinko/minecraft-server.git#subdirectory=ops"
```

recommend setting up a Discord Webhook for notifications:

```sh
discord_webhook=your-discord-webhook
```

run:

```sh
RCON_PASSWORD=$rcon_password \
WEBHOOK=$discord_webhook \
$HOME/venv/bin/python -m mcops.auto.shutdown
```

if you use OpenAI LLM:

```sh
$HOME/venv/bin/python -m pip install "mcops @ git+https://github.com/oshinko/minecraft-server.git#subdirectory=ops[openai]"
read -sp "OpenAI API Key: " openai_api_key; echo
```

run:

```sh
RCON_PASSWORD=$rcon_password \
OPENAI_API_KEY=$openai_api_key \
WEBHOOK=$discord_webhook \
$HOME/venv/bin/python -m mcops.auto.shutdown
```
