<?php
wfLoadExtension('EmulateGroup');
$wgEmulateGroupGroupList = function() {
  $groupNames = TorqueConfig::getConfiguredGroups();
  sort($groupNames);
  return $groupNames;
};
?>
