# Using the official Ubuntu base image
FROM ubuntu:20.04

# Setting environment variables
ENV DEBIAN_FRONTEND=noninteractive
# Install sudo 
RUN apt-get update && apt-get install -y sudo

# Create a non-root user and set its home directory
RUN useradd -m -s /bin/bash dockerastt

# Add the non-root user to the sudo group
RUN usermod -aG sudo dockerastt

RUN echo "dockerastt:TestingDocker" | chpasswd

RUN echo "dockerastt ALL=(ALL:ALL) ALL" >> /etc/sudoers

# Apt update
RUN apt update -y
RUN apt install software-properties-common -y

# Getting Lely canopen 
RUN add-apt-repository ppa:lely/ppa -y

#installing Python 3.10 and other dependencies
#RUN apt install python3.10 python3-pip iproute2 can-utils pkg-config python3-dcf-tools -y 
RUN apt install python3 python3-pip iproute2 can-utils pkg-config python3-dcf-tools -y 

# Setting the working directory
WORKDIR /app

# Changing ownership of the /app directory to the non-root user
RUN chown -R dockerastt:dockerastt /app

# Copying asst code into the container
COPY . /app

RUN pip3 install poetry==1.7.1
RUN poetry config virtualenvs.create false && poetry install

# Dependencies to build lely
RUN apt install git build-essential automake libtool python3-setuptools python3-wheel python3-empy python3-yaml libbluetooth-dev valgrind doxygen graphviz -y

# Get and build lely
#COPY installLely.sh /app/
RUN chmod +x /app/installLely.sh
RUN /app/installLely.sh

# Compile slave
RUN chmod +x /app/src/antenna_simulator/compileSlave.sh
RUN /app/src/antenna_simulator/compileSlave.sh 

# Define the command to run the application
COPY src/ /app/src/
COPY requirements.txt /app/src/
COPY src/ /app/src/component_managers/
# Install Python dependencies
RUN pip install --no-cache-dir -r /app/src/requirements.txt

ENV ASTT_PASSWORD="TestingDocker"

# Set the PYTHONPATH environment variable
ENV PYTHONPATH="/app/src/astt_gui:/app/src/component_managers:/app/src/antenna_simulator:$PYTHONPATH"

# Expose port 5000
EXPOSE 5000

# Switch to the non-root user
USER  dockerastt

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
