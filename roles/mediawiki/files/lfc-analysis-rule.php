<?php
# This establishes some new tabs, and removes the "Talk" tab for mediawiki pages.
#
# The two default tabs are the LFC Analysis and Extensions pages.
#
# This code works on the $wgLFCExtraTabs variable.  It should be a list of three item lists:
# * the first is the prepend of the proposal name
# * the second item will be the name of a tab linking to that page, if a page is found
# * the third is the namespace (conventionally one word, all lowercase, unique) for styling
#
# These pages are for supplemental information to the proposals, but which didn't belong on
# the proposal pages, and yet should be visually adjacent.
#
# You can extend this variable by doing something the lines of:
#
# $wgLFCExtraTabs[] = ["Page name prepend ", "Tab Name", "tabnamespace"];
#
# If one of the tabs included has the namespace 'main', then it will override
# the configuration for the default tab, such as showing up in a different location,
# with a different name.
#
# There's a codependency with the ETL pipelines that these pages actually
# need to exist on the wiki.

# The tabs get ordered in the order of the array.  This means you need to overwrite it
# completely if you'd like these tabs to appear elsewhere in the order
#
# If overridden by a function of zero arguments, that will get called (useful if the tabs
# shown depends on some runtime rules, like user group)
$wgLFCExtraTabs = function() {
  global $wgUser;

  # This permission "lfcanalysis" is set up in default-permissions
  if($wgUser->isSafeToLoad() && $wgUser->isAllowed("lfcanalysis")) {
    return [
      ["LFC Analysis of ", "LFC Analysis", "lfcanalysis"],
      ["Evaluations of ", "Evaluations", "evaluations"]
    ];
  } else {
    return [["Evaluations of ", "Evaluations", "evaluations"]];
  }
};

$wgHooks['SkinTemplateNavigation'][] = function ( $template, &$links ) {
  # Proposals should only be living in the main namespace
  if(!array_key_exists('main', $links['namespaces'])) {
    return;
  }
  global $wgLFCExtraTabs;

  $currentTitle = $template->getTitle()->getFullText();

  $originalPageTitle = $currentTitle;
  $main_tab_name = 'Proposal';

  if(is_callable($wgLFCExtraTabs)) {
    $wgLFCExtraTabs = call_user_func($wgLFCExtraTabs);
  }

  foreach($wgLFCExtraTabs as $tab) {
    if($tab[2] == 'main') {
      $main_tab_name = $tab[1];
    }
    $prepend = $tab[0];

    # If we're on a tab, then the main page # should be the original proposal.  If we
    # didn't have this, the main page would be the page we're looking at, even when
    # we're on a tab page (amusingly making new tabs for "Evaluations of Evaluations of <proposal")
    if (strlen($currentTitle) > strlen($prepend) && substr($currentTitle, 0, strlen($prepend)) === $prepend) {
      $originalPageTitle = substr($currentTitle, strlen($prepend));
      $links['namespaces']['main']['class'] = '';
      $links['namespaces']['main']['href'] = Title::newFromText($originalPageTitle)->getLocalUrl();
      break;
    }
  }

  # We need two loops because the first loop ascertains the original proposal title
  foreach($wgLFCExtraTabs as $tab) {
    if($tab[2] == 'main') {
      $main_tab = $links['namespaces']['main'];
      unset($links['namespaces']['main']);
      $links['namespaces']['main'] = $main_tab;
      continue;
    }

    $prepend = $tab[0];
    $tab_name = $tab[1];
    $tab_namespace = $tab[2];

    $tab_title = Title::newFromText($prepend . $originalPageTitle);
    $on_this_tab = ($currentTitle == $prepend . $originalPageTitle);

    # Add the tab to the top of the page.  If happen to be on the tab, then we should
    # reflect that visually.
    if($on_this_tab || $tab_title->exists()) {
      $links['namespaces']['main']['text'] = $main_tab_name;
      $links['namespaces'][$tab_namespace] = [
       'class' => ($on_this_tab ? 'selected' : ''),
       'href' => ($on_this_tab ? $template->getTitle()->getLocalUrl() : $tab_title->getLocalUrl()),
       'text' => $tab_name,
      ];
    }
  }

  # Remove the talk tab, even if the talk page exists
  unset($links['namespaces']['talk']);
};
?>
