<?php
$wgHooks['SidebarBeforeOutput'][] = function (Skin $skin, &$bar) {
    # Do this all inline here for now because it's quick, and it would actually
    # be more confusing to set up the entire javascript infrastructure.  The moment
    # we do more things with js, this should all get broken out and modularized
    # correctly!
    #
    # Also depending on jquery here, which should get loaded by mediawiki.
    $out  = "<div style='line-height: 1.125em; font-size: 0.75em'>";
    if(array_key_exists("globalview_summaryview", $_COOKIE)) {
      $out .= "<button style='width:130px'";
      # Setting the expiration to long ago works, but I do wish there were a better method to delete a cookie
      $out .= "onclick='document.cookie = \"globalview_summaryview=on; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;\";";
      $out .= "window.location.reload(true);";
      $out .= "'>Competition View</button>";
    } else {
      $out .= "<button style='width:130px'";
      $out .= "onclick='document.cookie = \"globalview_summaryview=on; path=/;\";";
      $out .= "window.location.reload(true);";
      $out .= "'>Summary View</button>";
    }
    $out .= "</div>";
    $bar['View'] = $out;
    return true;
};

if(array_key_exists("globalview_summaryview", $_COOKIE)) {
  $wgTorqueView = json_encode(array("wiki_key" => "GlobalView", "view" => "Summary"));
}
?>
