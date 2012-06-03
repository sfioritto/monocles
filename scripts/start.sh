#!/bin/bash

trap "networksetup -setwebproxystate Wi-Fi off" SIGHUP SIGINT SIGTERM
networksetup -setwebproxy Wi-Fi localhost 8080 on bob mcgee
python dev.py
