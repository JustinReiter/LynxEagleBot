#!/bin/bash

sleep 30 
pushd /home/pi/Desktop/LynxEagleBot/Jot
tmux new -d -s jot 'python3 bot.py'
popd

