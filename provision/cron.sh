#!/bin/bash

export PATH=$PATH:/usr/local/bin;

cd /moai && /bin/git pull
cd /moai && /bin/python moai.py
cd /moai && /bin/git add --all :/
cd /moai && /bin/git commit --message="moaiBOT"
cd /moai && /bin/git push origin master

/sbin/shutdown --reboot 03:05
