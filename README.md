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

### Automatic system shutdown

Installs a service that automatically shuts down the system when there are no players playing.

recommend setting up a Discord Webhook for notifications:

```sh
discord_webhook=your-discord-webhook
```

test run:

```sh
RCON_PASSWORD=$rcon_password \
WEBHOOK=$discord_webhook \
$HOME/venv/bin/python -m mcops.auto.shutdown
```

if you use OpenAI LLM:

```sh
$HOME/venv/bin/python -m pip install "mcops[openai] @ git+https://github.com/oshinko/minecraft-server.git#subdirectory=ops"
read -sp "OpenAI API Key: " openai_api_key; echo
```

test run:

```sh
RCON_PASSWORD=$rcon_password \
OPENAI_API_KEY=$openai_api_key \
WEBHOOK=$discord_webhook \
$HOME/venv/bin/python -m mcops.auto.shutdown
```

start timer:

```sh
sudo bash -c "cat << EOF > /etc/systemd/system/mcops-auto-shutdown.service
[Unit]
Description=Minecraft Server Auto Shutdown

[Service]
Environment=RCON_PASSWORD=$rcon_password
Environment=OPENAI_API_KEY=$openai_api_key
Environment=WEBHOOK=$discord_webhook
WorkingDirectory=$HOME/minecraft
ExecStart=$HOME/venv/bin/python -m mcops.auto.shutdown
Type=oneshot
User=`whoami`

[Install]
WantedBy=multi-user.target
EOF"

sudo sh -c "cat << EOF > /etc/systemd/system/mcops-auto-shutdown.timer
[Unit]
Description=Minecraft Server Auto Shutdown Timer

[Timer]
OnCalendar=hourly
AccuracySec=1s
Unit=mcops-auto-shutdown.service

[Install]
WantedBy=timers.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable mcops-auto-shutdown.timer
sudo systemctl restart mcops-auto-shutdown.timer
```
