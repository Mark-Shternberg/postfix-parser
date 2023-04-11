#!/bin/bash
colGreen="\033[32m"
colRed="\033[31m"
colYellow="\033[43m"
resetCol="\033[0m"

if [ `id -u` -ne 0 ]; then
  echo "$colRed This script can be executed only as root, Exiting..$resetCol"
  exit 1
fi

add-apt-repository ppa:deadsnakes/ppa

apt-get -qqq update
apt-get -qqq install -y python3.8 python3.8-dev python3.8-distutils

apt-get -qqq install python3-pip
python3.8 -m pip install -U pipenv

cd /home/mailparser/postfix-parser

runuser -u mailparser -- cd /home/mailparser/postfix-parser && pipenv install

mail_log="/var/log/mail.log"
read -p "Enter mail.log path (default: /var/log/mail.log): " mail_log
echo -e "MAIL_LOG=$mail_log" > .env
read -p "Enter Admin password: " admin_pass
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

install -m 644 /home/mailparser/postfix-parser/postfix-parser.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable postfix-parser.service

systemctl start postfix-parser
if [ $? -eq 0 ]
then
  echo -e "$colGreen [Installed and work] $resetCol"
  echo -e "$colYellow -!!!- strongly recommended to close port 8487 for non-admins -!!!- $resetCol"
else
  echo -e "$colRed Some errors! Check your configs and logs $resetCol"
fi

cron () {
    echo "Creating cron job ..."
    cat /etc/crontab | grep -qi '/tmp/lck_mailparser'
    if [[ $? != 0 ]]; then
    echo -e "$colYellow Cron job already exist. $resetCol"
    else
    echo "*  *   *   *   *    flock /tmp/lck_mailparser /home/mailparser/postfix-parser/run.sh cron" > /etc/cron.d/mailparser
    if [ $? -eq 0 ]; then
        echo -e "$colGreen Cron job successfully created $resetCol"
    else
        echo -e "$colRed Error for cron job. $resetCol"
        exit 1
    fi
fi
}

