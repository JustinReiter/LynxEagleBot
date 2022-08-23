#!/bin/bash

sleep 30 
pushd /home/pi/Desktop/LynxEagleBot/Jot
tmux kill-session -t jot

pip3 install -r requirements.txt

tmux new -d -s jot 'python3 bot.py'
popd

