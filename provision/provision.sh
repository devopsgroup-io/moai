echo -e "\n> configuring necessary packages"
# update packages
sudo yum update -y
# install git
sudo yum install -y git
# clone the moai project
if ! [ -d "/moai/.git" ]; then
    sudo git clone "/moai"
else
	cd "/moai" && git pull
fi
# install python
sudo yum install -y python
sudo yum install -y python-devel
sudo yum install -y python-setuptools
# install python matplotlib
sudo python -m pip install -U pip setuptools
sudo python -m pip install matplotlib
sudo python -m pip install matplotlib --upgrade
sudo python -m pip install pandas
sudo python -m pip install pandas --upgrade


echo -e "\n> configuring iptables-services"
# disable the baked in firewalld
sudo systemctl stop firewalld
sudo systemctl mask firewalld
# install the iptables-services
sudo yum install -y iptables-services
sudo systemctl enable iptables
sudo systemctl start iptables
# allow server/client ssh over 22
sudo iptables\
    --append INPUT\
    --protocol tcp\
    --dport 22\
    --jump ACCEPT
# allow server to use 127.0.0.1 or localhost, lo = loopback interface
sudo iptables\
    --append INPUT\
    --in-interface lo\
    --jump ACCEPT
# allow server to access the web for packages, updates, etc
sudo iptables\
    --append INPUT\
    --match state\
    --state ESTABLISHED,RELATED\
    --jump ACCEPT
# allow ntp over 123
sudo iptables\
    --append INPUT\
    --protocol udp\
    --dport 123\
    --jump ACCEPT
# now that everything is configured, we drop everything else (drop does not send any return packets, reject does)
sudo iptables --policy INPUT DROP
# save our newly created config
sudo service iptables save
# restart iptables service
sudo systemctl restart iptables


echo -e "\n> configuring fail2ban"
# install fail2ban
sudo yum install -y fail2ban
# ensure fail2ban starts during boot
sudo systemctl enable fail2ban
# ensure fail2ban starts during boot
sudo systemctl start fail2ban
# define fail2ban jails
sudo cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
banaction = iptables-multiport
# "bantime" is the number of seconds that a host is banned.
bantime  = 7200
# a host is banned if it has generated "maxretry" during the last "findtime" seconds.
findtime  = 3600
# "maxretry" is the number of failures before a host get banned.
maxretry = 5
# enable carefully selected filters
[sshd-ddos]
enabled = true
[sshd]
enabled = true
EOF
# restart fail2ban
sudo systemctl restart fail2ban
# output the fail2ban jails
sudo fail2ban-client status


echo -e "\n> configuring yum-cron"
# install yum-cron to apply updates nightly
sudo yum install -y yum-cron
sudo systemctl enable yum-cron.service
sudo systemctl start yum-cron.service
# auto download updates
sudo sed --in-place --expression='/^download_updates\s=/s|.*|download_updates = yes|' /etc/yum/yum-cron.conf
# auto apply updates
sudo sed --in-place --expression='/^apply_updates\s=/s|.*|apply_updates = yes|' /etc/yum/yum-cron.conf
# do not send any messages to stdout or email
sudo sed --in-place --expression='/^emit_via\s=/s|.*|emit_via = None|' /etc/yum/yum-cron.conf
# restart the service to re-read any new configuration
sudo systemctl restart yum-cron.service
