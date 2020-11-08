<?php
  $wgEnableUploads = true;
  $wgFileExtensions = array_merge($wgFileExtensions, array('doc', 'docx', 'html', 'pdf', 'xlsx'));
  $wgFileBlacklist = array();
  $wgMimeTypeBlacklist = array();
  $wgStrictFileExtensions = false;
  $wgTrustedMediaFormats = array('application/zip', 'text/html');
  $wgVerifyMimeType = false;
  $wgAllowJavaUploads = true;
  $wgCheckFileExtensions = false;
  $wgGroupPermissions['bot']['edit'] = true;
  $wgGroupPermissions['bot']['upload'] = true;
  $wgGroupPermissions['bot']['torquedataconnect-admin'] = true;
  $wgGroupPermissions['autoconfirmed']['reupload'] = true;
?>
