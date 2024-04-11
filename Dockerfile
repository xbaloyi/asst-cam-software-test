# Using the official Ubuntu base image
FROM ubuntu:20.04

# Setting environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Apt update and installing required packages
RUN apt update && \
    apt install -y software-properties-common python3 python3-pip iproute2 can-utils pkg-config python3-dcf-tools \
    git build-essential automake libtool python3-setuptools python3-wheel python3-empy python3-yaml \
    libbluetooth-dev valgrind doxygen graphviz

# Adding Lely repository and installing Lely CANopen tools
RUN add-apt-repository ppa:lely/ppa -y && \
    apt update && \
    apt install -y lely-canopen

# Setting the working directory
WORKDIR /app

# Copying the source code and requirements file into the container
COPY src/astt_gui/ /app
COPY requirements.txt /app

# Installing Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt poetry==1.7.1 && \
    poetry config virtualenvs.create false && \
    poetry install

# Building Lely
COPY installLely.sh /app/
RUN chmod +x /app/installLely.sh && \
    /app/installLely.sh

# Compile slave
COPY src/antenna_simulator/compileSlave.sh /app/
RUN chmod +x /app/compileSlave.sh && \
    /app/compileSlave.sh

# Define the command to run the application
CMD ["python3", "app.py"]
