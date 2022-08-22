#!/bin/bash

sleep 30 
pushd /home/pi/Desktop/LynxEagleBot/LEBot
tmux kill-session -t biggus
tmux new -d -s biggus 'python3 bot.py live'
popd
