<?php
$wgGroupPermissions["NewIdeas"]['read'] = true;
$wgGroupPermissions['NewIdeas']['edittorqueconfig'] = true;
$wgGroupPermissions['NewIdeas']['teamcomment'] = true;
$wgGroupPermissions['NewIdeas']['teamcommentseeusernames'] = true;
$wgGroupPermissions['NewIdeas']['picksome'] = true;
$wgGroupPermissions['NewIdeas']['view-special-log'] = true;
$wgGroupPermissions['NewIdeas']['torque-edit'] = true;
$wgGroupPermissions['NewIdeas']['emulategroup'] = true;
$wgGroupPermissions['NewIdeas']['lfcanalysis'] = true;

array_push($wgSimpleSAMLphp_SyncAllGroups_LocallyManaged, "NewIdeas");

$wgSimpleSAMLphp_GroupMap["NewIdeas"] = ['groups' => ['New Ideas']];
?>
