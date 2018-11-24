# MacFound

Repository of open source code specific to MacArthur Foundation
internal projects.

The code here is unlikely to be of general use, because it is highly
specific to the needs and datasets of the [MacArthur
Foundation](https://www.MacFound.org).  We release it as open source
anyway, because that's our usual practice and because some of it could
serve as an example or a template for other similar efforts.

* CSV->Wiki

  Right now the thing most likely to be useful in here is the
  CSV->wiki conversion system.

  Start from the [wiki-refresh](wiki-refresh) script and see how it
  drives first [fix-csv](fix-csv), which performs some one-time
  transformations to a specific CSV file from the MacArthur
  Foundation, then joins some supplemental data using the ever-handy
  [csvkit suite](https://github.com/wireservice/csvkit), and then runs
  the final CSV through the general-purpose script
  [csv2wiki](https://github.com/OpenTechStrategies/csv2wiki)
  to create pages in a [MediaWiki](https://www.mediawiki.org/)
  instance.
  
  To run `wiki-refresh`, you should first copy one of the
  `macfound-*-csv2wiki-config.tmpl` files to `csv2wiki-config` and
  edit the latter in the obvious ways.

  This system has been tested with MediaWiki 1.28.  There are a few
  notes in
  [csv2wiki](https://github.com/OpenTechStrategies/csv2wiki)'s
  documentation about things to watch out for with MediaWiki, e.g.,
  you might have to run MediaWiki's `rebuildall.php` script to get the
  categories feature working, some MediaWiki instances may have
  spam-prevention features enabled that prevent csv2wiki from creating
  pages containing URLs, etc.

* fix-csv

  This is a script that wiki-refresh uses to sanitize the csv for
  csv2wiki.  It takes the data we received from MacArthur and cleans
  up the HTML.  Then, wiki-refresh runs csv2wiki on the proper html to
  produce mediawiki input.  The fix-csv script should not emit
  markdown-formatted text.

## Dependencies

[fix-csv](fix-csv) requires:

* [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/)
* [MWClient](https://github.com/mwclient/mwclient)
* [Unidecode](https://pypi.python.org/pypi/Unidecode) 
* [csvkit](https://github.com/wireservice/csvkit)

To install all of these, do `pip install bs4 mwclient unidecode csvkit`.

* Mediawiki

  This code requires you to have a MediaWiki instance; we are using
  MediaWiki 1.28.2 for our production servers.  One thing you might
  want to do is go to the root of your MediaWiki code (something like
  `/usr/share/mediawiki` if you installed the Debian package, or
  `core` if you installed the latest bleeding edge from Git), and run

      patch -p1 < .../wiki_search_strip_tags.patch

  (that patch file is in the same directory as this README.md).  

  This will cause MediaWiki to strip HTML tags from the snippets that
  get displayed in search results.

* The "Collection" extension: printing PDF books from selected wiki pages

  You can create PDF books from selected wiki pages by using the
  "Collection" extension.  Getting it to work is a bit complex.
  Here's what we did:

  1) First, install upstream Collection.  We used [release
     6654fa8](https://www.mediawiki.org/wiki/Special:ExtensionDistributor?extdistname=Collection&extdistversion=REL1_28),
     which appears to be the right one for compatibility with
     MediaWiki 1.28.2.  There is also a [Git development repository for
     Collections](https://gerrit.wikimedia.org/r/mediawiki/extensions/Collection);
     if there's a project home page or other organizing surface for
     the extension,      please [let us
     know](https://github.com/OpenTechStrategies/MacFound/issues/new)
     (we haven't been able to find it).

  2) Make sure Collection is an active plugin in `.../mediawiki/-1.28.2/LocalSettings.php`: 

         # For the Collections extension.
         # See https://www.mediawiki.org/wiki/Extension:Collection.
         require_once "$IP/extensions/Collection/Collection.php";
         $wgCollectionMWServeCredentials = "wikibot:*** PASSWORD FOR SOME WIKI USER WITH R/W ACCESS ***";
         $wgCollectionMWServeURL = "http://105.243.179.144:8899"; # USE YOUR WIKI SERVER'S IP ADDRESS
         $wgCollectionMaxArticles = 250;
         
  3) Install the PDF-rendering back end:

         $ sudo su
         root# apt-get install pdftk python-pip stow supervisor
         root# pip install virtualenv
         root# mkdir -p /usr/local/stow/mwrender/src
         root# virtualenv /usr/local/stow/mwrender/src/mwlib
         root# cd /usr/local/stow/mwrender/src/mwlib
         root# source bin/activate
         (mwlib) root# pip install mwlib mwlib.rl pyfribidi # these are pediapress packages
         (mwlib) root# pip install "pillow<3.0.0" gevent==1.1.2 #downgrade some deps "you'll never get it, i guess this shit is too new"

  4) Install this patch into your newly installed `mwlib`:

         $ sudo patch -p0 < sapi.patch

     The file `sapi.patch` is found in the same directory as this
     README.md.  It patches
     `/usr/local/stow/mwrender/src/mwlib/lib/python2.7/site-packages/mwlib/net/sapi.py`.

  5) Set up symlinks for various binaries:

         $ sudo mkdir /usr/local/stow/mwrender/bin
         $ cd /usr/local/stow/mwrender/bin
         $ sudo printf "#!/bin/sh\n\n/usr/local/stow/mwrender/src/mwlib/bin/python /usr/local/stow/mwrender/src/mwlib/bin/$(basename $0) $@\n" > nserve
         $ sudo chmod a+x nserve
         $ sudo ln -s nserve mw-qserve
         $ sudo ln -s nserve mw-render
         $ sudo ln -s nserve nslave
         $ sudo ln -s ../src/mwlib/bin/mw-zip 
         $ cd ..
         $ sudo stow -R mwrender

  6) Set up supervisor:

         $ sudo systemctl enable supervisor # run supervisor at startup
         $ sudo systemctl restart supervisor  # run supervisor now
         $ sudo vim /etc/supervisor/conf.d/collections.conf
    
         # Make this be the contents of the new file:

             [program:nserve]
             directory=/usr/local/stow/mwrender/src/mwlib
             command=/usr/local/stow/mwrender/src/mwlib/bin/python bin/nserve
             autostart=true
             autorestart=false
             redirect_stderr=true
             redirect_stdout=true
             
             [program:mwqserve]
             directory=/usr/local/stow/mwrender/src/mwlib 
             command=/usr/local/stow/mwrender/src/mwlib/bin/python bin/mw-qserve
             autostart=true
             autorestart=false
             redirect_stderr=true
             redirect_stdout=true
             
             [program:nslave]
             directory=/usr/local/stow/mwrender/src/mwlib 
             command=/usr/local/stow/mwrender/src/mwlib/bin/python bin/nslave --cachedir=/var/cache/mwrender
             autostart=true
             autorestart=false
             redirect_stderr=true
             redirect_stdout=true
             
             [group:collections]
             programs=nserve,mwqserve,nslave

  7) Tell supervisor to use the new config and start the "collections" group of processes:

         $ sudo mkdir /var/cache/mwrender
         $ sudo chmod a+rwx /var/cache/mwrender
         $ sudo supervisorctl reread
         $ sudo supervisorctl update
         $ sudo supervisorctl restart collections:*

