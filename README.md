# Rasplay2
Rasplay is a music player frontent for Rasberry Pi. Main features:
    - Controls MPD (Music Player Daemon) to play music from a streaming local source (via UPNP) or from internet radio stations.
    - Displays current song and player status.
    - Internel radio browser and player
        - Browse and play radio stations from a predefined list.append
        - Browse internel-radio catalog by various categories (genre, country, language)
-   - Display controller for OLED screen (SSD1306)
    - Physical buttons control (GPIO)
    - Other functionalities
        - Transmission torrent client stats display
        - System info display
        - System control (shutdown, reboot)

## Installation 
- Install Rasplay2
```
sudo ./install.sh
vim /usr/local/etc/rasplay2/config.yaml # Edit config as needed
sudo systemctl enable rasplay2
sudo systemctl start rasplay2
journalctl -feu rasplay2
```

## System config
Install and configure MPD, eg config in /usr/local/share/rasplay2/contrib/mpd.conf

### Sudo config
For running prividedged commands under the rasplay2 user add the /usr/local/share/rasplay2/contrib/sudoers.d/rasplay2 to /etc/sudoers.d (and of course have sudo installed)

## Hardware config
