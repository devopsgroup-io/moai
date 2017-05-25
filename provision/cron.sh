#!/bin/bash

cd /moai && /bin/python moai.py
cd /moai && git add --all :/
cd /moai && git commit --message="moaiBOT"
cd /moai && git push master
