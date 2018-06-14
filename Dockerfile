FROM ubuntu:18.04

#Update
RUN apt-get update
RUN apt-get install nodejs -y
RUN apt-get install npm -y
RUN apt-get install python3 -y
RUN apt-get install python3-pip -y

#Install dependencies
COPY package.json /src/package.json
COPY requirements.txt /src/requirements.txt
RUN cd /src; npm install
RUN cd /src; pip3 install -r requirements.txt
RUN DEBIAN_FRONTEND=noninteractive apt-get install tzdata
#Bundle source
COPY . /src

WORKDIR /src

EXPOSE 3000
CMD [ "npm", "start" ]
