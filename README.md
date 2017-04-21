# MacFound

Repository of open source code specific to MacArthur Foundation
internal projects.

The code here is unlikely to be of general use, because it is highly
specific to the needs and datasets of the [MacArthur
Foundation](https://www.MacFound.org).  We release it as open source
anyway, because that's our usual practice and because some of it could
serve as an example or a template for other similar efforts.

* CSV->Wiki

  Right now the things most likely to be useful in here is the
  CSV->wiki conversion system.

  Start from the [wiki-refresh](wiki-refresh) script and see how it
  drives first [fix-csv](fix-csv), which performs some one-time
  transformations to a specific CSV file from the MacArthur
  Foundation, and then runs the transformed CSV through the
  general-purpose script
  [csv2wiki](https://github.com/OpenTechStrategies/csv2wiki)
  to create pages in a [MediaWiki](https://www.mediawiki.org/)
  instance.

  This system has been tested with MediaWiki 1.28.  There are a few
  notes in
  [csv2wiki](https://github.com/OpenTechStrategies/csv2wiki)'s
  documentation about things to watch out for with MediaWiki, e.g.,
  you might have to run MediaWiki's `rebuildall.php` script to get the
  categories feature working, some MediaWiki instances may have
  spam-prevention features enabled that prevent csv2wiki from creating
  pages containing URLs, etc.
