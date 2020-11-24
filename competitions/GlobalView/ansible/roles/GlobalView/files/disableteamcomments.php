<?php

// Because team comments tags show up in rendered pages from the other wikis,
// and Global View doesn't install teamcomments, an empty <teamcomments /> tag
// shows up on all the proposals.
//
// This adds a parser hook for that tag, and effectively makes it do nothing.
$wgHooks['ParserFirstCallInit'][] = 'disableTeamCommentsParserFirstCallInit';

function disableTeamCommentsParserFirstCallInit( Parser $parser ) {
  $parser->setHook( "teamcomments", function($input, $args, $parser, $frame) { return ""; });
}
?>
