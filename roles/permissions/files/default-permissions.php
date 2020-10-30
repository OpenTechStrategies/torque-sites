<?php
# Even if these groups aren't used in the wiki (no users assigned), this should be the
# master list of all groups enabled on the wiki
$wgGroupPermissions['LFCConsultingPartners']['read'] = true;
$wgGroupPermissions['LFCResearchPartners']['read'] = true;
$wgGroupPermissions['LFCEvaluators']['read'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['read'] = true;
$wgGroupPermissions['DecisionMakers']['read'] = true;
$wgGroupPermissions['OutsideReviewers']['read'] = true;

$wgGroupPermissions['*']['read'] = false;
$wgGroupPermissions['bot']['protect'] = true;
$wgRestrictionLevels[] = 'generated';
$wgGroupPermissions['bot']['generated'] = true;

# Disable teamcomments for users on this wiki by default.
$wgGroupPermissions['*']['teamcomment'] = false;
$wgGroupPermissions['*']['teamcommentseeusernames'] = false;

# Log permissions (ability to see Special:Log)
$wgAvailableRights[] = 'view-special-log';
$wgGroupPermissions['*']['view-special-log'] = false;

# Configuration of different user groups
$wgGroupPermissions['sysop']['generated'] = true;
$wgGroupPermissions['sysop']['edittorqueconfig'] = true;
$wgGroupPermissions['sysop']['torquedataconnect-admin'] = true;
$wgGroupPermissions['sysop']['teamcomment'] = true;
$wgGroupPermissions['sysop']['teamcommentseeusernames'] = true;
$wgGroupPermissions['sysop']['picksome'] = true;
$wgGroupPermissions['sysop']['picksome-admin'] = true;
$wgGroupPermissions['sysop']['view-special-log'] = true;

$wgGroupPermissions['DecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['DecisionMakers']['teamcommentseeusernames'] = true;
$wgGroupPermissions['DecisionMakers']['picksome'] = true;
$wgGroupPermissions['DecisionMakers']['picksome-write'] = true;

$wgGroupPermissions['PseudoDecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['teamcommentseeusernames'] = true;

$wgGroupPermissions['LFCConsultingPartners']['torquedataconnect-edit'] = true;

$wgGroupPermissions['LFCResearchPartners']['teamcomment'] = true;

$wgGroupPermissions['LFCEvaluators']['teamcomment'] = true;

# Disable Special:Log for groups that don't have view-special-log above
$wgHooks['SpecialPage_initList'][] = function ( &$list ) {
  global $wgUser;

  if(!$wgUser->isAllowed('view-special-log')) {
    unset( $list['Log'] );
  }
  return true;
};

# This is the SimpleSAMLphp group mapping.  This is how incoming groups
# from SSO map to mediawiki groups.
$wgSimpleSAMLphp_SyncAllGroups_LocallyManaged = [
  "sysop",
  "bureaucrat",
  "interface-admin",
  "DecisionMakers",
  "LFCConsultingPartners",
  "LFCResearchPartners",
  "LFCEvaluators",
  "PseudoDecisionMakers",
];

$wgSimpleSAMLphp_GroupMap = [
  'sysop' => ['groups' => ['LFC Torque Admin', 'LFC Staff']],
  'interface-admin' => ['groups' => ['LFC Torque Admin', 'LFC Staff']],
  'bureaucrat' => ['groups' => ['LFC Torque Admin', 'LFC Staff']],
  'DecisionMakers' => ['groups' => ['LFC Decision Makers']],
  'LFCEvaluators' => ['groups' => ['LFC Consultants']]
];

?>
