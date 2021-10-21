<?php
# Even if these groups aren't used in the wiki (no users assigned), this should be the
# master list of all groups enabled on the wiki

# Deprecated groups
$wgGroupPermissions['LFCConsultingPartners']['read'] = true;
$wgGroupPermissions['LFCResearchPartners']['read'] = true;
$wgGroupPermissions['LFCEvaluators']['read'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['read'] = true;
$wgGroupPermissions['DecisionMakers']['read'] = true;
$wgGroupPermissions['OutsideReviewers']['read'] = true;

# Groups after reorg
$wgGroupPermissions["TorqueAdmin"]['read'] = true;
$wgGroupPermissions["LfcStaff"]['read'] = true;
$wgGroupPermissions["TorqueDecisionMaker"]['read'] = true;
$wgGroupPermissions["TorquePartner"]['read'] = true;
$wgGroupPermissions["TorqueDiligenceFinancial"]['read'] = true;
$wgGroupPermissions["TorqueDiligenceNonFinancial"]['read'] = true;
$wgGroupPermissions["TorqueBasic"]['read'] = true;

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
# DEPRECATED
$wgGroupPermissions['sysop']['generated'] = true;
$wgGroupPermissions['sysop']['edittorqueconfig'] = true;
$wgGroupPermissions['sysop']['torquedataconnect-admin'] = true;
$wgGroupPermissions['sysop']['teamcomment'] = true;
$wgGroupPermissions['sysop']['teamcommentseeusernames'] = true;
$wgGroupPermissions['sysop']['picksome'] = true;
$wgGroupPermissions['sysop']['picksome-admin'] = true;
$wgGroupPermissions['sysop']['view-special-log'] = true;
$wgGroupPermissions['sysop']['torquedataconnect-edit'] = true;
$wgGroupPermissions['sysop']['emulategroup'] = true;
$wgGroupPermissions['DecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['DecisionMakers']['teamcommentseeusernames'] = true;
$wgGroupPermissions['DecisionMakers']['picksome'] = true;
$wgGroupPermissions['DecisionMakers']['picksome-write'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['teamcommentseeusernames'] = true;
$wgGroupPermissions['LFCConsultingPartners']['torquedataconnect-edit'] = true;
$wgGroupPermissions['LFCResearchPartners']['teamcomment'] = true;
$wgGroupPermissions['LFCEvaluators']['teamcomment'] = true;

# For reorganization
$wgGroupPermissions['TorqueAdmin']['generated'] = true;
$wgGroupPermissions['TorqueAdmin']['edittorqueconfig'] = true;
$wgGroupPermissions['TorqueAdmin']['torquedataconnect-admin'] = true;
$wgGroupPermissions['TorqueAdmin']['teamcomment'] = true;
$wgGroupPermissions['TorqueAdmin']['teamcommentseeusernames'] = true;
$wgGroupPermissions['TorqueAdmin']['picksome'] = true;
$wgGroupPermissions['TorqueAdmin']['picksome-admin'] = true;
$wgGroupPermissions['TorqueAdmin']['view-special-log'] = true;
$wgGroupPermissions['TorqueAdmin']['torquedataconnect-edit'] = true;
$wgGroupPermissions['TorqueAdmin']['emulategroup'] = true;

$wgGroupPermissions['LfcStaff']['edittorqueconfig'] = true;
$wgGroupPermissions['LfcStaff']['teamcomment'] = true;
$wgGroupPermissions['LfcStaff']['teamcommentseeusernames'] = true;
$wgGroupPermissions['LfcStaff']['picksome'] = true;
$wgGroupPermissions['LfcStaff']['view-special-log'] = true;
$wgGroupPermissions['LfcStaff']['torquedataconnect-edit'] = true;
$wgGroupPermissions['LfcStaff']['emulategroup'] = true;

$wgGroupPermissions['TorqueDecisionMaker']['teamcomment'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['teamcommentseeusernames'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['picksome'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['picksome-write'] = true;

$wgGroupPermissions['TorquePartner']['teamcomment'] = true;
$wgGroupPermissions['TorquePartner']['picksome'] = true;


# Disable Special:Log for groups that don't have view-special-log above
$wgHooks['SpecialPage_initList'][] = function ( &$list ) {
  global $wgUser;

  if($wgUser->isSafeToLoad() && !$wgUser->isAllowed('view-special-log')) {
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
  # Deprecated groups
  "DecisionMakers",
  "LFCConsultingPartners",
  "LFCResearchPartners",
  "LFCEvaluators",
  "PseudoDecisionMakers",

  # After the reorganization
  "sysop",
  "bureaucrat",
  "interface-admin",
  "TorqueAdmin",
  "LfcStaff",
  "TorqueDecisionMaker",
  "TorquePartner",
  "TorqueDiligenceFinancial",
  "TorqueDiligenceNonFinancial",
  "TorqueBasic"
];
#
# And this is the mapping (MediaWiki on left, incoming SSO on right):
#
$wgSimpleSAMLphp_GroupMap = [
  # Deprecated settings
  'sysop' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'interface-admin' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'bureaucrat' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],
  'DecisionMakers' => ['groups' => ['LFC Decision Makers', 'Board Members']],
  'PseudoDecisionMakers' => ['groups' => ['LFC Pseudo Decision Makers', 'Pseudo Board Members']],
  'LFCEvaluators' => ['groups' => ['LFC Evaluators']],
  'LFCConsultingPartners' => ['groups' => ['LFC Consultants']],
  'LFCResearchPartners' => ['groups' => ['LFC Research Partners']],
  'LFCTorqueAdmin' => ['groups' => ['LFC Torque Admin', 'LFC Staff', 'LFC Admins']],

  # After the reorganization
  'sysop' => ['groups' => ['Torque Admin']],
  'interface-admin' => ['groups' => ['Torque Admin']],
  'bureaucrat' => ['groups' => ['Torque Admin']],
  'TorqueAdmin' => ['groups' => ['Torque Admin']],
  'LfcStaff' => ['groups' => ['LfC Staff']],
  'TorqueDecisionMaker' => ['groups' => ['Torque Decision Maker']],
  'TorquePartner' => ['groups' => ['Torque Partner']],
  'TorqueDiligenceFinancial' => ['groups' => ['Torque Diligence - Financial']],
  'TorqueDiligenceNonFinancial' => ['groups' => ['Torque Diligence - Non-Financial']],
  'TorqueBasic' => ['groups' => ['Torque Basic']]
];

?>
