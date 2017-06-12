echo -e "\n> configuring package repositories"
# define package repositories
sudo yum install -y epel-release
# update packages
sudo yum update -y


echo -e "\n> configuring time"
# set timezone
sudo timedatectl set-timezone "America/New_York"
# install ntp
sudo yum install -y ntp
sudo systemctl enable ntpd.service
sudo systemctl start ntpd.service


echo -e "\n> system email configuration"
# install postfix
sudo yum install -y postfix
sudo systemctl enable postfix.service
sudo systemctl start postfix.service
sudo cat > "/root/.forward" << EOF
blackhole@devopsgroup.io
EOF
sudo systemctl reload postfix.service


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
touch /etc/fail2ban/jail.local
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


echo -e "\n> system swap configuration"
# get current swaps
swaps=$(swapon --noheadings --show=NAME)
swap_volumes=$(cat /etc/fstab | grep "swap" | awk '{print $1}')
# create a 1024MB swap at /swapfile1024 if it does not exist
if [[ ! ${swaps[*]} =~ "/swapfile1024" ]]; then
    echo -e "the swap /swapfile1024 does not exist, creating..."
    sudo dd if=/dev/zero of=/swapfile1024 count=1024 bs=1MiB
    sudo chmod 0600 /swapfile1024
    sudo mkswap /swapfile1024
fi
sudo swapon /swapfile1024
# add the swap /swapfile1024 to startup if it does not exist
if [[ ! ${swap_volumes[*]} =~ "/swapfile1024" ]]; then
    sudo bash -c 'echo -e "\n/swapfile1024 swap    swap    defaults    0   0" >> /etc/fstab'
fi
# define the swaps
defined_swaps=("/swapfile1024")
# remove all swaps except the defined swaps
while read -r swap; do
    if [[ ! ${defined_swaps[*]} =~ "${swap}" ]]; then
        echo -e "only the ${defined_swaps[*]} swap files should exist, removing ${swap}..."
        sudo swapoff "${swap}"
    fi
done <<< "${swaps}"
# remove all swap volumes from startup except the defined swaps
while read -r swap_volume; do
    if [[ ! ${defined_swaps[*]} =~ "${swap_volume}" ]]; then
        echo -e "only the ${defined_swaps[*]} swap files should exist, removing ${swap_volume}..."
        # escape slashes for sed
        swap_volume=$(echo -e "${swap_volume}" | sed 's#\/#\\\/#g')
        # remove swap volumes that don't match the defined swaps
        sed --in-place "/${swap_volume}/d" /etc/fstab
    fi
done <<< "${swap_volumes}"
# output the resulting swap
swapon --summary
# tune the swap temporarily for runtime
# https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Performance_Tuning_Guide/s-memory-tunables.html
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50
# tune the swap permanently for boot
sudo cat > "/etc/sysctl.d/catapult.conf" << EOF
vm.swappiness=10
vm.vfs_cache_pressure=50
EOF


echo -e "\n> configuring required packages"
# install python
sudo yum install -y gcc
sudo yum install -y openssl-devel
sudo yum install -y python
sudo yum install -y python-devel
sudo yum install -y python-setuptools
sudo easy_install pip
# install python packages
sudo python -m pip install -U pip setuptools
sudo python -m pip install matplotlib
sudo python -m pip install matplotlib --upgrade
sudo python -m pip install pandas
sudo python -m pip install pandas --upgrade
sudo python -m pip install pygeoip
sudo python -m pip install pygeoip --upgrade
sudo python -m pip install pyopenssl
sudo python -m pip install pyopenssl --upgrade
sudo python -m pip install pyyaml
sudo python -m pip install pyyaml --upgrade
sudo python -m pip install requests
sudo python -m pip install requests --upgrade
sudo python -m pip install requests[security]
sudo python -m pip install requests[security] --upgrade


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


echo -e "\n> system known hosts configuration"
# initialize known_hosts
sudo mkdir -p ~/.ssh
sudo touch ~/.ssh/known_hosts
# ssh-keyscan github.com for a maximum of 10 tries
i=0
until [ $i -ge 10 ]; do
    sudo ssh-keyscan -4 -T 10 github.com >> ~/.ssh/known_hosts
    if grep -q "github\.com" ~/.ssh/known_hosts; then
        echo "ssh-keyscan for github.com successful"
        break
    else
        echo "ssh-keyscan for github.com failed, retrying!"
    fi
    i=$[$i+1]
done


echo -e "\n> configuring moai"
# install git
sudo yum install -y git
git config --global user.email "blackhole@devopsgroup.io"
git config --global user.name "moaiBOT"
# clone the moai project
if ! [ -d "/moai/.git" ]; then
    sudo git clone "https://github.com/devopsgroup-io/moai.git" "/moai"
    cd "/moai" && git remote set-url origin "git@github.com:devopsgroup-io/moai.git"
else
    cd "/moai" && git pull
fi


echo -e "\n> decrypt secrets"
# decrypt secrets
gpg --verbose --batch --yes --passphrase ${1} --output ~/.ssh/id_rsa --decrypt /moai/secrets/id_rsa.gpg
chmod 400 ~/.ssh/id_rsa


echo -e "\n> configuring moai cron job"
cat "/moai/provision/cron.sh" > "/etc/cron.daily/moai.cron"
chown root:root "/etc/cron.daily/moai.cron"
chmod 755 "/etc/cron.daily/moai.cron"
