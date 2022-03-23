<?php

function lfc( &$title, &$article, &$output, &$user, $request, $mediaWiki ) {
        $view = "";
        $group = "";
  if(!$user->isLoggedIn()) {
          $view = "Demo";
          $group = "sysop";
  } else {
    $view = TorqueConfig::getCurrentView(); 
    $group = TorqueConfig::getValidGroup($user); 
  }
  if($view == "Demo" &&
    preg_match("/(\d)/", $title->getText())) {
    global $wgTorqueGroup, $wgTorqueView, $wgTorqueRaw;
    $wgTorqueRaw = true;
    $wgTorqueView = $view;
    $wgTorqueGroup = $group;

    $page = new WikiPage($title);

    # This is a prototype.  We circumvent all of mediawiki at this point to just
    # dump out the skin we want and then get out as fast as possible.
    #
    # The Right Way would be to create an actual mediawiki skin that does
    # the kinds of things we want, and choose that skin for public users.
    include "demo_header.php";
    $parser = \MediaWiki\MediaWikiServices::getInstance()->getParser();
    $po= $parser->parse($page->getContent()->getText(), $title, ParserOptions::newFromUser($user));
    echo $po->getText();
    include "demo_footer.php";
    exit();
  }
}

$wgHooks['BeforeInitialize'][] = 'lfc';
?>
