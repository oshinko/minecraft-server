# Minecraft Server

Amazon Linux 2023 & t4g.small:

```sh
sudo dnf update -y
sudo dnf install java-17-amazon-corretto-devel -y

sudo timedatectl set-timezone Asia/Tokyo

curl -O https://api.papermc.io/v2/projects/paper/versions/1.19.4/builds/547/downloads/paper-1.19.4-547.jar

java -jar paper-1.19.4-547.jar  # すぐに停止し、規約への同意を要求される

sed -i s/eula=false/eula=true/g eula.txt  # 同意
```

テスト起動:

```sh
java -Xmx1500M -jar paper-1.19.4-547.jar
```

サービス化:

```sh
sudo bash -c "cat << EOF > /etc/systemd/system/minecraft.service
[Unit]
Description=Minecraft Server

[Service]
WorkingDirectory=$HOME
ExecStart=`which java` -Xmx2G -jar $HOME/paper-1.19.4-547.jar
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
