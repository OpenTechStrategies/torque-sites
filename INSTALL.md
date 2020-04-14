# Installing torque-sites

The torque sites are meant to be installed in relatively few commands, with
each ansible playbook doing all of the hard lifting.

First the support systems need to be installed, and then the competitions
can be.  While not every competition needs every support system, at this time
they all reside on one machine, so managing the interdependencies is too
much overhead.

## Installing via ansible

Each project directory with an ansible sub directory with the same
layout.

* `<projectname>.yml` - the main playbook file
* `inv/` - the inventory files
* `roles/` - the ansible scripts and support

Before you get started, you need to get ansible on your system.  This
is probably easiest through package management.

```
$ sudo apt-get install ansible
```

### Local installs

In order to install locally, two things need to happen.  First
copy over the inventory variable template file and edit it:

```
$ cp inv/local/group_vars/all{.tmpl,}
$ $EDITOR inv/local/group_vars/all
```

Each template file includes documentation about what the variables do.

Second, use ansible-playbook to run the installation

```
$ ansible-playbook <projectname>.yml -i inv/local
```

### Production installs (for OTS only)

There are a few more steps to install on production because there's
secrets needed.

First, the `$OTSUSER` needs to be set up (see the onboarding docs
for more information).  This user is the one which you have an
account on the target machines with ssh and sudo access granted.
They should all be the same account name.  Set the variable in
whatever environment file you use.

Second, [opass](https://github.com/OpenTechStrategies/ots-tools/blob/master/opass)
needs to be installed.  You will also need to have all the files
in `clients/macfound/torque-sites` be accessible with your key.

Third, for the competition installs (NOT for supporting system installs)
you need to get the secrets and put them where ansible can find them.
For a given environment, it will look something like this:

```
$ opass show clients/macfound/torque-sites/<project-name>/ansible/<environment> > inv/<environment>/group_vars/all/secret
```

The name of the file (secret) is added to .gitignore so you don't
accidentally commit it.

And finally, run ansible-playbook

```
$ ansible-playbook <projectname>.yml -i inv/<environment>
```

## Running the ETL pipeline (for OTS only)

For each competition, there is an `etl` subdirectory that includes all the
code to decrypt, combine, and upload the data.  There's a number of
prerequisite steps.

### System setup

First, set up your `$OTSDIR` (see onboarding for more information).
Then you need to check out the macfound torque-sites

```
$ mkdir -p $OTSDIR/clients/macfound/
$ svn co https://svn.opentechstrategies.com/repos/ots/trunk/clients/macfound/torque-sites $OTSDIR/clients/macfound/
```

Then you need to get the OTS utilities that includes `get-bigdata`
```
$ svn co https://svn.opentechstrategies.com/repos/ots/trunk/utils $OTSDIR/
```

Now get the confidential data for the site you're working on.

```
$ cd $OTSDIR/clients/macfound/torque-sites/<competition-name>/data
$ $OTSDIR/utils/get-bigdata
```

Install necessary system libraries
```
# For Debian
$ sudo apt-get gpg unzip install python3-pip ansible acl
```

Install csv2wiki using pip
```
$ git checkout https://github.com/OpenTechStrategies/csv2wiki
$ cd csv2wiki ; pip3 install -e .
```

Lastly, set up a directory where you want the encrypted data to go

```
$ mkdir ~/data
```

### Running the ETL pipeline

Now you can run the etl pipeline from the competition you're in, which
will always be in the `deploy` script.

First, you need to configure it to the target wiki.

```
$ cd <competition>/etl
$ cp csv2wiki-config.tmpl csv2wiki-config
$ $EDITOR csv2wiki-config
```

And run the script

```
$ cd <competition>/etl

# Whatever data directory you set up above
$ ./deploy ~/data
```

# Installing the system

In order to get the base system up and running, you need to use the install
from ansible instructions above for the following:

* mwlib
* torque
* simplesaml

## NOTE about simplesaml secrets in other environments

The simplesaml inventories do need secrets, but they aren't stored in the
normal place in opass.  Instead, you need to edit the secret file and
put in the values from `opass show clients/macfound/torque-sites/simplesamlsalt`

```
$ $EDITOR simplesaml/inv/<environment>/group_vars/all/secret
```

# Installing a competition

For the competition you're working with, run the instructions from
"Installing via Ansible" and "Running the ETL pipeline" above.
