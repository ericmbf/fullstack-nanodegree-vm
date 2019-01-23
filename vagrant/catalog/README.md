# Catalog

# Installing the Vagrant VM for run the catalog project.

### Git

If you don't already have Git installed, [download Git from git-scm.com.](http://git-scm.com/downloads) Install the version for your operating system.

You will need Git to install the configuration for the VM.

### VirtualBox

VirtualBox is the software that actually runs the VM. [You can download it from virtualbox.org, here.](https://www.virtualbox.org/wiki/Downloads)  Install the *platform package* for your operating system.  You do not need the extension pack or the SDK. You do not need to launch VirtualBox after installing it.

### Vagrant

Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem.  [You can download it from vagrantup.com.](https://www.vagrantup.com/downloads) Install the version for your operating system.

## Fetch the Source Code and VM Configuration

From the terminal, run:

    git clone https://github.com/ericmbf/fullstack-nanodegree-vm.git

This will give you a directory named **catalog** inside vagrant folder.

## Run the virtual machine!

Using the terminal, go to vagrant directory and type **vagrant up** to build the vagrant VM.

## Running the Catalog App

After build process from vagrant, type **vagrant ssh** to enter to VM. After using tha application maybe you want to go out from VM. Using **vagrant halt** fot it.

Now you can go to python file typing **cd /vagrant/catalog**. You can see the **insertCategories.py** file. Execute this script to create the database with some categories and items, typing **python insertCategories.py**. After this, you can start the web flask application type **python application.py**.

You can acess the web page in your browser visiting the **http://localhost:8000** URL.
You should be able to view, add, edit, and delete items from catalog.