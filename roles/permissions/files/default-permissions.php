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
$wgGroupPermissions["LfcPartner"]['read'] = true;
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
$wgGroupPermissions['*']['lfcanalysis'] = false;

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
$wgGroupPermissions['TorqueAdmin']['lfcanalysis'] = true;

$wgGroupPermissions['LfcStaff']['edittorqueconfig'] = true;
$wgGroupPermissions['LfcStaff']['teamcomment'] = true;
$wgGroupPermissions['LfcStaff']['teamcommentseeusernames'] = true;
$wgGroupPermissions['LfcStaff']['picksome'] = true;
$wgGroupPermissions['LfcStaff']['view-special-log'] = true;
$wgGroupPermissions['LfcStaff']['torquedataconnect-edit'] = true;
$wgGroupPermissions['LfcStaff']['emulategroup'] = true;
$wgGroupPermissions['LfcStaff']['lfcanalysis'] = true;

$wgGroupPermissions['TorqueDecisionMaker']['teamcomment'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['teamcommentseeusernames'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['picksome'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['picksome-write'] = true;
$wgGroupPermissions['TorqueDecisionMaker']['lfcanalysis'] = true;

$wgGroupPermissions['LfcPartner']['teamcomment'] = true;
$wgGroupPermissions['LfcPartner']['picksome'] = true;
$wgGroupPermissions['LfcPartner']['lfcanalysis'] = true;

$wgGroupPermissions['TorqueDiligenceFinancial']['lfcanalysis'] = true;

$wgGroupPermissions['TorqueDiligenceNonFinancial']['lfcanalysis'] = true;


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
  # After the reorganization
  "sysop",
  "bureaucrat",
  "interface-admin",
  "TorqueAdmin",
  "LfcStaff",
  "TorqueDecisionMaker",
  "LfcPartner",
  "TorqueDiligenceFinancial",
  "TorqueDiligenceNonFinancial",
  "TorqueBasic"
];
#
# And this is the mapping (MediaWiki on left, incoming SSO on right):
#
$wgSimpleSAMLphp_GroupMap = [
  # After the reorganization.  When it's complete, uncomment the next three item.
  # They had to be commented because they were interfernig the the above deprecated settings
  # and causing failures for admins and staff.
  'sysop' => ['groups' => ['Torque Admin']],
  'interface-admin' => ['groups' => ['Torque Admin']],
  'bureaucrat' => ['groups' => ['Torque Admin']],
  'TorqueAdmin' => ['groups' => ['Torque Admin']],
  'LfcStaff' => ['groups' => ['LfC Staff']],
  'TorqueDecisionMaker' => ['groups' => ['Torque Decision Maker']],
  'LfcPartner' => ['groups' => ['LfC Partner']],
  'TorqueEvaluator' => ['groups' => ['Torque Evaluator']],
  'TorqueDiligenceFinancial' => ['groups' => ['Torque Diligence - Financial']],
  'TorqueDiligenceNonFinancial' => ['groups' => ['Torque Diligence - Non-Financial']],
  'TorqueBasic' => ['groups' => ['Torque Basic']]
];

?>
