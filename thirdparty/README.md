### Thirdparty files

These are general files, usually downloaded from the internet, that
support the ansible scripts.  The reason we download and commmitted
them to this repository rather than downloading them at time of deploy
is to have a reliable cache.  Ideally, this cache would be on a webserver
somewhere under our control, and then this repository would be more
compact, but this is a good stop gap for now.

These are files that are independent of competitions, usually used
by multiple.  For files that a single competition depends on, it may
live in one of these directories or in the competitions ansible tree.

The current set includes:

* extensions - mediawiki extensions not developed by OTS
* simplesaml - the tar for simplesamlphp

