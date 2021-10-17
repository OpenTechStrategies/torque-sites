<?php
wfLoadExtension('EmulateGroup');
$wgEmulateGroupGroupList = function() {
  $groupNames = TorqueDataConnectConfig::getConfiguredGroups();
  sort($groupNames);
  return $groupNames;
};
?>
