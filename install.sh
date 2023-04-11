#!/bin/bash
colGreen="\033[32m"
colRed="\033[31m"
colYellow="\033[1;33m"
resetCol="\033[0m"

if [ `id -u` -ne 0 ]; then
  echo "$colRed This script can be executed only as root, Exiting..$resetCol"
  exit 1
fi

wget -qO- https://download.rethinkdb.com/repository/raw/pubkey.gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/rethinkdb-archive-keyrings.gpg

echo "deb [signed-by=/usr/share/keyrings/rethinkdb-archive-keyrings.gpg] https://download.rethinkdb.com/repository/ubuntu-$(lsb_release -cs)\
 $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list

add-apt-repository ppa:deadsnakes/ppa

apt-get -qqq update
apt-get -qqq install -y python3.8 python3.8-dev python3.8-distutils rethinkdb

apt-get -qqq install python3-pip
python3.8 -m pip install -U pipenv

cd /home/mailparser/postfix-parser

sudo -H -u mailparser bash -c 'cd /home/mailparser/postfix-parser && pipenv install'

read -p "Enter mail.log path (default: /var/log/mail.log): " mail_log
if [[ $mail_log == '' ]]; then mail_log="/var/log/mail.log"; fi
echo -e "MAIL_LOG=$mail_log" > .env
read -p "Enter Admin password: " admin_pass
echo -e "ADMIN_PASS=$admin_pass" >> .env
host=$(hostname  -I | cut -f1 -d' ')
echo -e "HOST=$host" >> .env
secret_key=$(echo $RANDOM | md5sum | head -c 20)
echo -e "SECRET_KEY=$secret_key" >> .env
echo -e "RETHINK_HOST=localhost\nRETHINK_DB=maildata\nVUE_DEBUG=false" >> .env

while true; do
    read -p "Do you need to lock temp file (for large logs)? [Yy/Nn]: " accept
    case $accept in
        [yY] ) cron;;
        [nN] ) break;;
        * ) echo -e " $colRed Type only Y or N !$resetCol";;
    esac
done

chown -R mailparser:mailparser /home/mailparser/postfix-parser

install -m 644 /home/mailparser/postfix-parser/postfix-parser.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable postfix-parser.service

systemctl start postfix-parser
if [ $? -eq 0 ]
then
  echo -e "$colGreen [Installed and work] $resetCol"
  echo -e "$colYellow -!!!- strongly recommended to close port 8487 for non-admins -!!!-\nWeb UI available from: http://$host:8487 $resetCol"
else
  echo -e "$colRed Some errors! Check your configs and logs $resetCol"
fi

cron () {
    echo "Creating cron job ..."
    echo "*  *   *   *   *    flock /tmp/lck_mailparser /home/mailparser/postfix-parser/run.sh cron" > /etc/cron.d/mailparser
    if [ $? -eq 0 ]; then
        echo -e "$colGreen Cron job successfully created $resetCol"
    else
        echo -e "$colRed Error for cron job. $resetCol"
        exit 1
    fi
}
