# Installing torque

Installation is done using ansible.  While you can execute these instructions as
a developer, the best way is to use ansible so we continue to keep the playbooks
up to date.  For that reason, when adding something to the installation, instead
add it to the correct role and so that other developers can just re-run and pull
your changes.

## Assumptions torque makes

At this time, certain things are assumed and can later be configured.

* www-data is the user for apache
* apache uses /var/www/html for it's root directory
* The installed system is Debian or Ubuntu
* lfc is the name of the wiki, so http://domain.tld/lfc/ is the location of the wiki
* All four groups are installed on the same machine
  * mediawiki config assumes that mysql and mwlib are running locally

# Setting up your system

## Installing ansible

You can most likely just use the ansible provided by your distro:

```ShellSession
 $ sudo apt-get install ansible
```

## Setting up your hosts file

The easiest way to create a local ansible hosts file, by using one of the templates
in the current directory.  You can make this global by copying to `/etc/ansible/hosts`

```
$ cp hosts.localhost.tmpl hosts
```

or, if you'd prefer to use a different machine / user:
```
$ cp hosts.rempte.tmpl hosts
$ edit hosts
```

You'll see four groups, for mediawiki, mysql, simplesaml, and mwlib.  This is so you
the four services can be broken apart later for dockerization as needed.

You may have as many hosts as you like within the groups.  You should have
SSH access to those hosts with your current user, either via keys or ssh-agent.
You can test the connection to them with `ansible -i hosts mediawiki -m ping`.
You should see something like the following for each host in your `[mediawiki]`
group:

```
example.com | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
```

You also need to have sudo access for those users.  You can either update the
sudoers file to not need a password, or use `--ask-become-pass` when running the
ansible-playbook command.

## Setting up needed variables

All the configurable variables for torque live in `group_vars/all`, and you can
generate that file via:

```ShellSesssion
 $ cp group_vars/all.tmpl group_vars/all
```

Look in that file for information about the variables and how you can set them

### Note for OTS deployers about variables/secrets

While ansible does have the ability to encrypt secrets so they can be checked in,
OTS has decided not to do that, and instead uses opass to hold the pertinent
information. 

After that, you can run:

```
   $ ansible-playbook all.yml -i /path/to/inventories/<environment>
```

# Running the playbook

The one liner to run the playbook:

```ShellSesssion
 $ ansible-playbook -i hosts all.yml
```

# Viewing the mediawiki instance

You should, at this time, be able to go to http://<host>/lfc/ and see mediawiki.
