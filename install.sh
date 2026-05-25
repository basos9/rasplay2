#!/bin/bash
set -x 
BASE=$(readlink -f "$(dirname "$0")")
pushd $BASE
install -d /usr/local/share/rasplay2
install *py requirements.txt /usr/local/share/rasplay2/
install -d /usr/local/etc/rasplay2
install config.yaml.dist /usr/local/etc/rasplay2/config.yaml.dist
install config.yaml.dist /usr/local/etc/rasplay2/config.yaml
python3 -m venv /usr/local/share/rasplay2/venv
/usr/local/share/rasplay2/venv/bin/python3 -m pip install -r /usr/local/share/rasplay2/requirements.txt
install rasplay2.service /etc/systemd/system/
if getent passwd rasplay2 >/dev/null; then
    #echo "User rasplay2 already exists"
    usermod -s /usr/sbin/nologin rasplay2
else
    useradd -r -s /usr/sbin/nologin rasplay2
fi
systemctl daemon-reload
systemctl status rasplay2.service
