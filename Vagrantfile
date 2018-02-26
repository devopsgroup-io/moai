# -*- mode: ruby -*-
# vi: set ft=ruby :

# load user.yml
@user = YAML.load_file("secrets/user.yml")

# encrypt secrets.yml
#`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/secrets.yml.gpg --armor --cipher-algo AES256 --symmetric secrets/secrets.yml`
# decrypt secrets.yml
`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/secrets.yml --decrypt secrets/secrets.yml.gpg`

# encrypt id_rsa
#`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/id_rsa.gpg --armor --cipher-algo AES256 --symmetric secrets/id_rsa`
# decrypt id_rsa
`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/id_rsa --decrypt secrets/id_rsa.gpg`

# encrypt id_rsa.pub
#`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/id_rsa.pub.gpg --armor --cipher-algo AES256 --symmetric secrets/id_rsa.pub`
# decrypt id_rsa.pub
`gpg --verbose --batch --yes --passphrase "#{@user["gpg_key"]}" --output secrets/id_rsa.pub --decrypt secrets/id_rsa.pub.gpg`

# load secrets.yml
@secrets = YAML.load_file("secrets/secrets.yml")

Vagrant.configure("2") do |config|

  config.vm.define "moai" do |config|
    config.vm.provider :digital_ocean do |provider,override|
      override.vm.box = "digital_ocean"
      override.vm.box_url = "https://github.com/devopsgroup-io/vagrant-digitalocean/raw/master/box/digital_ocean.box"
      override.ssh.private_key_path = "secrets/id_rsa"
      provider.ssh_key_name = "moai"
      provider.token = "#{@secrets["digital_ocean_token"]}"
      provider.image = "centos-7-x64"
      provider.region = "nyc3"
      provider.size = "s-1vcpu-1gb"
      provider.ipv6 = true
      provider.private_networking = true
      provider.backups_enabled = false
    end
    config.vm.synced_folder ".", "/vagrant", disabled: true
    config.vm.provision "shell", path: "provision/provision.sh", args: ["#{@user["gpg_key"]}"]
  end

end
