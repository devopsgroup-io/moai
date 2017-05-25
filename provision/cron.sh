#!/bin/bash

cd /moai && /bin/python moai.py
cd /moai && /bin/git add --all :/
cd /moai && /bin/git commit --message="moaiBOT"
cd /moai && /bin/git push origin master
