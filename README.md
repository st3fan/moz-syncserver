[![Build Status](https://travis-ci.org/st3fan/moz-syncserver.svg?branch=master)](https://travis-ci.org/st3fan/moz-syncserver)

# moz-syncserver

This is a standalone server for Firefox Sync.

> This project is in early stages and may have bugs leading to data
  loss. Personally I use it to succesfully sync my Firefox profile
  between three devices. If you are adventurous, please give it a try
  and [file bugs](https://github.com/st3fan/moz-syncserver/issues) and
  feature requests.

## Requirements

The server has been developed with Go 1.3.1 and runs on all the
platforms that Go supports. This includes Linux, FreeBSD, OS X and
Windows.

It is recommended to run the server behind a front proxy like for
example Nginx. It is also highly recommended to secure the server with
TLS.

The server currently only supports PostgreSQL as the storage
backend. It has been tested with PostgreSQL 9.3 but should be fine
with 8.0 and up.

## Manual Installation

These instructions are for Ubuntu 14.04.1 LTS but should be easy to
apply to other systems. At some time later there will be installable
packages and a Docker image.

### Database Setup

```
# Install PostgreSQL
sudo apt-get install postgesql

# Create a syncserver user and database, choose your own password
sudo -u postgres psql -c "create user syncserver with password 'syncserver';" -U postgres
sudo -u postgres psql -c 'create database syncserver owner syncserver;' -U postgres

# Load the setup script, create the tables
wget https://raw.githubusercontent.com/st3fan/moz-syncserver/master/setup.sql
sudo -u postgres psql -f setup.sql -U syncserver -d syncserver
```

### Sync Server Daemon Setup

First, download and install the server. This assumes 64-bit x86 Linux.

```
sudo mkdir -p cd /usr/local/sbin
cd /usr/local/sbin
wget TODO INSERT LINK TO RELEASE HERE
```

Create a configuration file named `/etc/syncserver.ini` and put the following contents in it:

```
[SyncServer]
ListenAddress = 127.0.0.1
ListenPort = 5000
PublicHostname = https://sync.example.com
SharedSecret = ThisIsAnImportantSecretThatYouShouldChange
DataSource = postgres://syncserver:syncserver@localhost/syncserver
```

> It is important to change the `PublicHostname`, `SharedSecret` and `DataSource` settings.

Then, configure Upstart:

```
cd /etc/init
sudo wget https://raw.githubusercontent.com/st3fan/moz-syncserver/master/etc/upstart/syncserver.conf
sudo service syncserver start
```

### Setup Nginx

```
# Install Nginx
sudo apt-get install nginx

# Download and activate the example nginx configuration
cd /etc/nginx/sites-available/
sudo wget TODO INSERT LINK TO UPSTART SCRIPT HERE
cd /etc/nginx/sites-enabled/
sudo ln -s ../sites-available/syncserver.conf

*edit syncserver.conf to change the hostname and certificate/key path*
sudo vi syncserver.conf

# Restart the server
sudo service syncserver start
```

Check if everything is running ok by calling the `/version` API endpoint:

```
curl https://sync.sateh.com/version; echo
{"version":"0.1"}
```

Firefox Configuration
---------------------

You tell Firefox to use a custom Sync Server by changing the Token
Server endpoint URL. To do this, go to the hidden settings by opening
the `about:config` url. Then search for the
`services.sync.tokenServerURL` setting and change it to:

> `https://your.server.com/token/1.0/sync/1.5`

You should now be able to connect to sign in to Firefox Sync and your
personal Sync Server will be used.

Please note that even though you run your own server, Firefox will
still use the Mozilla hosted Firefox Accounts.

