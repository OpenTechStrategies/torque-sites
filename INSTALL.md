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
* `roles/` - the ansible scripts for customizations specific to this competition

Before you get started, you need to get ansible on your system.  This
is probably easiest through package management.  We recommend you install ansible 2.9.x or above.

```
$ sudo apt-get install ansible
```

Then, you need to tell ansible where to find the general torque-sites roles

```
$ export ANSIBLE_ROLES_PATH=$ANSIBLE_ROLES_PATH:/path/to/torque-sites/roles
```

#### Apache configuration for large files

Because the etl pipelines we use generate large csvs to upload, and those are
normally bigger than the default allowed upload size in php.  For that reason,
after you install apache, you need to make sure that our installed .htaccess
files overload the php configuration.

You need to add this line

```
AllowOverride All
```

to the permissions of your apache directory, in a section that looks like

```
<Directory /var/www/html>
    # Options ...
    AllowOverride All
</Directory>
```

Or set the php values `upload_max_filesize` and `post_max_size` to appropriate
values in whatever php configuration you are using.

### Local installs

In order to install locally, two things need to happen.  First
copy over the inventory variable template file and edit it:

```
$ cp inv/local/group_vars/all{.tmpl,}
$ $EDITOR inv/local/group_vars/all
```

Each template file includes documentation about what the variables do.

The templates are structured so that you can leverage the [envsubst](https://www.gnu.org/software/gettext/manual/html_node/envsubst-Invocation.html) utility to populate placeholder values if you prefer.  For instance:

```
$ envsubst < inv/local/group_vars/all.tmpl > inv/local/group_vars/all
```

Second, use ansible-playbook to run the installation

```
$ ansible-playbook <projectname>.yml -i inv/local
```

### Production installs (for OTS only)

There are a few more steps to install on production because there's
secrets needed.

First, the `$OTS_USERNAME` needs to be set up (see the onboarding docs
for more information).  This user is the one which you have an
account on the target machines with ssh and sudo access granted.
They should all be the same account name.  Set the variable in
whatever environment file you use.

Second, [opass](https://github.com/OpenTechStrategies/ots-tools/blob/master/opass)
needs to be installed.  You will also need to have all the files
in `clients/lever-for-change/torque-sites` be accessible with your key.

Third, for the competition installs (NOT for supporting system installs)
you need to get the secrets and put them where ansible can find them.
For a given environment, it will look something like this:

```
$ opass show clients/lever-for-change/torque-sites/<project-name>/ansible/<environment> > inv/<environment>/group_vars/all/secret
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

First, set up your `$OTS_DIR` (see onboarding for more information).
Then you need to check out the LFC torque-sites repository

```
$ mkdir -p $OTS_DIR/clients/lever-for-change
$ svn co https://svn.opentechstrategies.com/repos/ots/trunk/clients/lever-for-change/torque-sites $OTS_DIR/clients/lever-for-change/torque-sites
```

Then you need to get the OTS utilities that includes `get-bigdata`
```
$ git clone https://github.com/OpenTechStrategies/ots-tools.git $OTS_TOOLS_DIR
```

Now get the confidential data for the site you're working on.

```
$ cd $OTS_DIR/clients/lever-for-change/torque-sites/<competition-name>/data
$ $OTS_TOOLS_DIR/get-bigdata
```

Install necessary system libraries
```
# For Debian
$ sudo apt-get gpg unzip install python3-pip ansible acl
```

Install the main etl pipeline using pip
```
$ cd etl ; pip3 install -e .
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
$ cd competitions/<competition>/etl
$ cp config.py.tmpl config.py
$ $EDITOR config.py
```

And run the script

```
$ cd competitions/<competition>/etl

# Whatever data directory you set up above
$ ./deploy ~/data
```

Note, running `deploy` with no arguments will give you the list of args available
or required.  In some projects, more than just the `data` directory is needed.

For most scripts, both `-c` and `-p` options are available.  The former uploads
the spreadsheet only, not uploading attachments or creating wiki pages.  The
latter allows you to include a paring option.  This option, if a number, reduces
the set of keys to `1/NUMBER`.  If it starts with a `+`, you can add a number of
comma separated keys to pare to, and if it starts with an `@`, then it is a file
with a new line separated list of keys, both of which will reduce it to only
the included keys.

# Installing the system

In order to get the base system up and running, you need to use the install
from ansible instructions above for the following:

* base/mwlib
* base/torquedata
* base/simplesaml

## NOTE about simplesaml secrets in other environments

The simplesaml inventories do need secrets, but they aren't stored in the
normal place in opass.  Instead, you need to edit the secret file and
put in the values from `opass show clients/lever-for-change/torque-sites/simplesamlsalt`

```
$ $EDITOR base/simplesaml/inv/<environment>/group_vars/all/secret
```

# Installing a competition

## Competition installation

For the competition you're working with, run the instructions from
"Installing via Ansible" and "Running the ETL pipeline" above.

## Local Login

If you have not set up 3rd party login, you can access [local login instead](https://github.com/OpenTechStrategies/torque-sites/blob/main/DESIGN.md#local-login-ie-regular-non-okta-mediawiki-login-is-also-possible)

# Creating a new competition

See the [template competition README](competitions/template/README.md)
