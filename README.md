# Rasplay2
Rasplay is a music player frontent for Rasberry Pi. See below for hardware configuration. Main features:
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
Currently this works with a ssd1306 OLED display wired on the I2C pins for display and with a 7 buttons pad (left,right,up,down,mid,set,rst). Display is rendering 4 1/2 rows with a default font size.

## WIRING for DISPLAY (128x64)
1.3 inch oled IIC Serial White OLED Display Module 128X64 I2C SSD1306 12864 LCD Screen Board VDD GND SCK SDA for Arduino Black
GPIO physical BCD - cable - DISPLAY pinout SSD1306 128X64 
1 VCC3         - blue - 4
3 GPIO02(SDA1) - purple - 1
5 GPIO03(SCL1) - grey  - 2
9 GND          - white - 3

### WIRING for BUTTONS (7 buttons)
NOYITO 5-Channel Five Direction Button Module 5D Rocker Joystick Development Board - Up Down Left Right Center Click Switch Module 

GPIO physical BCD  - BUTTON (ROTATED BUTTON)
34 Ground - purple - COM/GND 1 
32 GPIO12 - grey   - UP 2 (LEFT)
33 GPIO13 - blue   - DWN 3 (RIGHT)
31 GPIO6  - green  - LEFT 4 (UP)  was 
36 GPIO16 - yellow - RGT 5 (DOWN)
37 GPIO26 - orange - MID 6
38 GPIO20 - red    - SET 7
40 GPIO21 - brown  - RST 8
---
other pins
35 GPIO19 