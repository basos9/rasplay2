#!/bin/bash
set -x 
BASE=$(readlink -f "$(dirname "$0")")
pushd $BASE
install -d /usr/local/share/rasplay2
install *py requirements.txt /usr/local/share/rasplay2/
install -d /usr/local/etc/rasplay2
install config.yaml.dist /usr/local/etc/rasplay2/config.yaml.dist
if ! [ -f /usr/local/etc/rasplay2/config.yaml ]; then
   install config.yaml.dist /usr/local/etc/rasplay2/config.yaml
fi
python3 -m venv /usr/local/share/rasplay2/venv
/usr/local/share/rasplay2/venv/bin/python3 -m pip install -r /usr/local/share/rasplay2/requirements.txt
install -m 644 rasplay2.service /etc/systemd/system/
if getent passwd rasplay2 >/dev/null; then
    #echo "User rasplay2 already exists"
    usermod -s /usr/sbin/nologin rasplay2
else
    useradd -r -s /usr/sbin/nologin rasplay2
fi
if getent group i2c >/dev/null; then
    #echo "Group i2c already exists"
    usermod -a -G i2c rasplay2
fi
if getent group gpio >/dev/null; then
    #echo "Group gpio already exists"
    usermod -a -G gpio rasplay2
fi
cat <<EOL > /etc/sudoers.d/rasplay2
# Allow rasplay2 to run shutdown and reboot without password
rasplay2 ALL=(ALL) NOPASSWD: /sbin/shutdown, /sbin/reboot, /sbin/systemctl ^restart (upmpdcli|mpd)$
EOL

systemctl daemon-reload
if systemctl is-active rasplay2.service ; then
   systemctl restart rasplay2.service
fi
systemctl status rasplay2.service

