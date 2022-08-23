#!/bin/bash

sleep 30 
pushd /home/pi/Desktop/LynxEagleBot/LEBot
tmux kill-session -t biggus

pip3 install -r requirements.txt

tmux new -d -s biggus 'python3 bot.py live'
popd
