#!/bin/bash

trap "networksetup -setwebproxystate Wi-Fi off" SIGHUP SIGINT SIGTERM
networksetup -setwebproxy Wi-Fi localhost 8080 off
sudo python proxy.py
