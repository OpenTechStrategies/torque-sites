# MacFound

Repository of open source code specific to MacArthur Foundation
internal projects.

The code here is unlikely to be of general use, because it is highly
specific to the needs and datasets of the [MacArthur
Foundation](https://www.MacFound.org).  We release it as open source
anyway, because that's our usual practice and because some of it could
serve as an example or a template for other similar efforts, primarily
for anyone deploying a
[torque](https://github.com/OpenTechStrategies/torque) enabled
MediaWiki installation.

## Dependencies

[compose-csvs](compose-csvs) requires:

* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
* [MWClient](https://github.com/mwclient/mwclient)
* [Unidecode](https://pypi.python.org/pypi/Unidecode)

To install all of these, do `pip install bs4 mwclient unidecode`.

### csv2wiki

`wiki-refresh` requires csv2wiki, which can be gotten from github,
and then installed as a package on your system.

```
$ get clone https://github.com/OpenTechStrategies/csv2wiki
$ cd csv2wiki
$ pip3 install -e . # From csv2wiki README
```

### Configuration

To run `wiki-refresh`, you should first copy
`macfound-torquedata-csv2wiki-config.tmpl` to
`macfound-torquedata-csv2wiki-config` and edit the latter
in the obvious ways.  The credentials will come from however
you configured ansible when installing the torque system.

## Running

After the encryped data is unencryped in a data directory somewhere,
simply run:

```
$ ./wiki-refresh /path/to/unencrypted/data
```

## Components

* wiki-refresh

  Start from the [wiki-refresh](wiki-refresh) script and see how it
  drives first [compose-csvs](compose-csvs), which performs some one-time
  transformations to specific CSVa file from the MacArthur Foundation,
  as well as joining them with some supplemental data, and then uploads
  the final CSV to a running torque server.  After which is creates
  proposal pages using
  [csv2wiki](https://github.com/OpenTechStrategies/csv2wiki), that
  each have a single line that calls into the torque server.

* torque

  This system depends on a running
  [torque](https://github.com/OpenTechStrategies/torque) system, with
  mediawiki installed.  It uses the TorqueDataConnect extensionsion
  to upload the spreadsheet and tocs after generating them.

* compose-csvs

  This is a script that wiki-refresh uses to sanitize and combine csvs
  for use.  You need to have access to the files listed in it to create
  the final proposal csv, as well as all the TOC json data to upload
  to the torque server.

  Look at the file for more information, especially the usage section
  and how wiki-refresh uses it.

* upload-csvs

  After compose-csvs has generated all the files, upload-csvs is
  responsible for taking the generated files and sending them to
  the running torque/mediawiki server.

  This also uploads all the attachments specific to the MacArthur
  foundation.
