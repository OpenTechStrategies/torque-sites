<?php

# Make it so names of log types are more amenable to LFC users
$logTitlesOverrideMessages = [
  "picksomelogpage" => "Selection",
  "activitylogpage" => "Misc. Activity (page views, login, logout, etc)",
  "simplefavoriteslog" => "Favorites",
  "log-name-create" => "Page Creation",
  "movelogpage" => "Page Rename",
  "uploadlogpage" => "File Upload",
  "dellogpage" => "Page Deletion",
  "newuserlogpage" => "User Creation",
  "log-name-teamcomments" => "Comments",
  "torquedataconnect-apiaccesslog" => "API Accesses",
  "torquedataconnect-datachangeslog" => "Data Changes",
  "rightslog" => "Changes to Access Control / Permissions"
];

$wgHooks['MessagesPreLoad'][] = function($title, &$message, $code) {
  global $logTitlesOverrideMessages;
  if(array_key_exists(strtolower($title), $logTitlesOverrideMessages)) {
    $message = $logTitlesOverrideMessages[strtolower($title)];
  }
};


# Remove log types that we don't want
$logTypesBlacklist = ["block", "contentmodel", "import", "managetags", "merge", "patrol", "protect", "rights", "tag"];

$wgHooks['SetupAfterCache'][] = function () {
  global $wgLogTypes, $logTypesBlacklist;
  foreach($logTypesBlacklist as $logType) {
    unset($wgLogTypes[array_search($logType, $wgLogTypes)]);
  }

  return true;
};

# Change the log format a little
#
# This is a little brittle, based on how the lines are rendered by the skin currently used
# but should work for the foreseeable future.
$wgHooks['LogEventsListLineEnding'][] = function ($page, &$line, &$entry, &$classes, &$attribs){
  $line = preg_replace('/(\d\d\d\d)/', '\1 &mdash;', $line, 1);
};
?>
