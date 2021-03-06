This documents how to install the AI Cloud management system.
# 0. pre-requisite
```
#install python3
sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm
sudo yum install -y python36u
sudo yum install -y python36u-pip
sudo yum install -y python36u-devel
sudo ln -s /usr/bin/python3.6 /usr/bin/python3
sudo python3 -m pip install flask flask-wtf pyyaml gunicorn
```

# 1. download from github
```
cd ~
mkdir workspace
cd workspace
git clone https://github.com/lihoukun/CloudAI.git
```

# 2. deploy the system
```
vi config_bj.sh # and update wherever neccessary
source config_bj.sh

# deploy all 
./bin/exaai.sh all

# or deploy what is needed
./bin/exaai.sh pv
./bin/exaai.sh kubeboard
./bin/exaai.sh jupyter
./bin/exaai.sh flask
```

# 3. ngrok for http
```
# write ngrok yaml fiel, in US, the file at ~/.ngrok2/ngrok.yml, and the content is below
tunnels:
  ui:
    addr: cnumf01:80
    proto: http
    hostname: exaai.ap.ngrok.io
    auth: "exaai:exaai"
  notebook:
    addr: cnumf01:30088
    proto: http
    hostname: notebook.exaai.ap.ngrok.io
    auth: "exaai:exaai"
  tensorboard:
    addr: cnumf01:30060
    proto: http
    hostname: tensorboard.exaai.ap.ngrok.io
    auth: "exaai:exaai"
  nginx:
    addr: cnumf01:30080
    proto: http
    hostname: nginx.exaai.ap.ngrok.io
  kubeboard:
    addr: cnumf01:8001
    proto: http
    hostname: kubeboard.exaai.ap.ngrok.io
    auth: "exaai:exaai"

# start ngrok for http
ngrok start --all
```

# 4. open the browser and visit 'exaai.ap.ngrok.io'

