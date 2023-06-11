# Minecraft Server

Amazon Linux 2023 & t4g.small:

```sh
# パッケージをインストール
sudo dnf update -y
sudo dnf install java-17-amazon-corretto-devel -y

# タイムゾーンを設定
sudo timedatectl set-timezone Asia/Tokyo

# ゲームディレクトリを作成
mkdir minecraft
cd minecraft

# サーバーをダウンロード
curl -o paper.jar https://api.papermc.io/v2/projects/paper/versions/1.20/builds/8/downloads/paper-1.20-8.jar

# 初回起動
java -jar paper.jar  # すぐに停止し、規約への同意を要求される

# 規約に同意
sed -i s/^eula=false$/eula=true/g eula.txt

# RCON を有効化
read -sp "rcon.password: " password; echo  # パスワードを設定

sed -i \
    -e "s/^rcon.password=$/rcon.password=$password/g" \
    -e s/^enable-rcon=false$/enable-rcon=true/g \
    server.properties
```

テスト起動:

```sh
java -Xmx2G -jar paper.jar
```

サービス化:

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
