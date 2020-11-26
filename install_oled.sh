#!/bin/bash

start_time="$(date +"%T")"

cd oled
bash install.sh > install_log.txt
cd ..

printf "\n\n-----------------------------------------\n"
echo started at $start_time finished at "$(date +"%T")"
echo "You should reboot now. Enjoy your display and have a nice day."
exit 0