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

# API-using groups
# These are local login users (as that's required to use api.php) and so
# will not have corresponding entries in the saml config
$wgGroupPermissions['API_Candid']['read'] = true;
$wgGroupPermissions['API_ForumOne']['read'] = true;
$wgGroupPermissions['API_ScalingScience']['read'] = true;
$wgGroupPermissions['API_KFG']['read'] = true;
$wgGroupPermissions['API_OTS']['read'] = true;

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
$wgGroupPermissions['sysop']['torquedataconnect-edit'] = true;

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

# We have to convert incoming groups from SSO (e.g., MacFound Okta) to
# Mediawiki (SimpleSAMLphp) groups.  The incoming groups often have
# spaces in their names, to make them more readable to users, whereas
# MediaWiki groups can't have spaces.  Also, in some cases there are
# existing well-known MediaWiki groups (e.g., "sysop") that map pretty
# well to an incoming SSO group, even though the two names are
# unrelated, so in those cases we just convert the incoming group to
# the MediaWiki group.
#
# (For more information on SimpleSAML configuration in general, see
# https://www.mediawiki.org/wiki/Extension:SimpleSAMLphp#Configuration.)
# 
# These are the MediaWiki Groups:
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
#
# And this is the mapping (MediaWiki on left, incoming SSO on right):
#
$wgSimpleSAMLphp_GroupMap = [
  'sysop' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'interface-admin' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'bureaucrat' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'DecisionMakers' => ['groups' => ['LFC Decision Makers', 'Board Members']],
  'PseudoDecisionMakers' => ['groups' => ['LFC Pseudo Decision Makers', 'Pseudo Board Members']],
  'LFCEvaluators' => ['groups' => ['LFC Evaluators']],
  'LFCConsultingPartners' => ['groups' => ['LFC Consultants']],
  'LFCResearchPartners' => ['groups' => ['LFC Research Partners']]
];

?>
