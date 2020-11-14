<?php

function lfc( &$title, &$article, &$output, &$user, $request, $mediaWiki ) {
	$view = "";
	$group = "";
  if(!$user->isLoggedIn()) {
	  $view = "Demo";
	  $group = "sysop";
  } else {
    $view = TorqueDataConnectConfig::getCurrentView(); 
    $group = TorqueDataConnectConfig::getValidGroup($user); 
  }
  if($view == "Demo" &&
    preg_match("/(\d)/", $title->getText())) {
    global $wgTorqueDataConnectGroup, $wgTorqueDataConnectView, $wgTorqueDataConnectRaw;
    $wgTorqueDataConnectRaw = true;
    $wgTorqueDataConnectView = $view;
    $wgTorqueDataConnectGroup = $group;

    $page = new WikiPage($title);

    # This is a prototype.  We circumvent all of mediawiki at this point to just
    # dump out the skin we want and then get out as fast as possible.
    #
    # The Right Way would be to create an actual mediawiki skin that does
    # the kinds of things we want, and choose that skin for public users.
    include "demo_header.php";
    echo $output->parse($page->getContent()->getText());
    include "demo_footer.php";
    exit();
  }
}

$wgHooks['BeforeInitialize'][] = 'lfc';
?>
