<?php
$wgGroupPermissions['*']['read'] = false;
$wgGroupPermissions['bot']['protect'] = true;
$wgRestrictionLevels[] = 'generated';
$wgGroupPermissions['bot']['generated'] = true;

# Permissions that we want sysops/admins to have that
# but not for staff go here
$wgGroupPermissions['sysop']['generated'] = true;
$wgGroupPermissions['sysop']['edittorqueconfig'] = true;
$wgGroupPermissions['sysop']['torquedataconnect-admin'] = true;

# Groups requested specifically by LFC.
$wgGroupPermissions['LFCConsultingPartners']['read'] = true;
$wgGroupPermissions['LFCConsultingPartners']['torquedataconnect-edit'] = true;
$wgGroupPermissions['LFCResearchPartners']['read'] = true;
$wgGroupPermissions['LFCEvaluators']['read'] = true;

# These are OTS Torque Standard Groups
$wgGroupPermissions['OutsideReviewers']['read'] = true;
$wgGroupPermissions['Staff']['read'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['read'] = true;
$wgGroupPermissions['DecisionMakers']['read'] = true;

# Disable teamcomments for users on this wiki by default.
$wgGroupPermissions['*']['teamcomment'] = false;
$wgGroupPermissions['*']['teamcommentseeusernames'] = false;

# Then enable teamcomments for the groups that should be leaving comments
$wgGroupPermissions['Staff']['teamcomment'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['DecisionMakers']['teamcomment'] = true;
$wgGroupPermissions['sysop']['teamcomment'] = true;
$wgGroupPermissions['LFCResearchPartners']['teamcomment'] = true;
$wgGroupPermissions['LFCEvaluators']['teamcomment'] = true;

# Allow some groups to see usernames
$wgGroupPermissions['Staff']['teamcommentseeusernames'] = true;
$wgGroupPermissions['PseudoDecisionMakers']['teamcommentseeusernames'] = true;
$wgGroupPermissions['DecisionMakers']['teamcommentseeusernames'] = true;
$wgGroupPermissions['sysop']['teamcommentseeusernames'] = true;

# PickSome permissions
$wgGroupPermissions['DecisionMakers']['picksome'] = true;
$wgGroupPermissions['DecisionMakers']['picksome-write'] = true;
$wgGroupPermissions['sysop']['picksome'] = true;
$wgGroupPermissions['sysop']['picksome-admin'] = true;

# Log permissions (ability to see Special:Log)
$wgAvailableRights[] = 'view-special-log';
$wgGroupPermissions['*']['view-special-log'] = false;
$wgGroupPermissions['sysop']['view-special-log'] = true;

# Disable Special:Log for groups that don't have view-special-log above
$wgHooks['SpecialPage_initList'][] = function ( &$list ) {
  global $wgUser;

  if(!$wgUser->isAllowed('view-special-log')) {
    unset( $list['Log'] );
  }
  return true;
};
?>
