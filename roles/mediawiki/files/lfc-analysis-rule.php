<?php
# This establishes some new tabs, and removes the "Talk" tab for mediawiki pages.
#
# The two tabs are the LFC Analysis and Extensions pages.  This code looks for those pages
# to exist on the wiki, and if they do, adds them to the tabs at the top.  These pages
# are for supplemental information to the proposals, but which didn't belong on the proposal
# pages, and yet should be visually adjacent.

$wgHooks['SkinTemplateNavigation'][] = function ( $template, &$links ) {
  $currentTitle = $template->getTitle()->getFullText();

  # There's a codependency with the ETL pipelines that these pages actually
  # need to exist on the wiki.
  $lfc_prepend = "LFC Analysis of ";
  $eval_prepend = "Evaluations of ";

  $isAnalysisPage = (strlen($currentTitle) > strlen($lfc_prepend) && substr($currentTitle, 0, strlen($lfc_prepend)) === $lfc_prepend);
  $isEvalPage = (strlen($currentTitle) > strlen($eval_prepend) && substr($currentTitle, 0, strlen($eval_prepend)) === $eval_prepend);

  $originalPageTitle = $currentTitle;

  # If we're on the analysis page, or the evaluation page, then the main page
  # should be the original proposal.  If we didn't have this, the main page would be
  # the page we're looking at, even with we're on the Analysis Page/Evaluations Page.
  if($isAnalysisPage) {
    $originalPageTitle = substr($currentTitle, strlen($lfc_prepend));
    $links['namespaces']['main']['class'] = '';
    $links['namespaces']['main']['href'] = Title::newFromText($originalPageTitle)->getLocalUrl();
  } else if($isEvalPage) {
    $originalPageTitle = substr($currentTitle, strlen($eval_prepend));
    $links['namespaces']['main']['class'] = '';
    $links['namespaces']['main']['href'] = Title::newFromText($originalPageTitle)->getLocalUrl();
  }
  $lfcAnalysisTitle = Title::newFromText($lfc_prepend . $originalPageTitle);
  $evalTitle = Title::newFromText($eval_prepend . $originalPageTitle);

  # If we're on the Analysis page, then we shouldn't add another analysis page for the analysis
  # page were on.  Visually, we should be on the tab, with the left tab being the proposal
  if($isAnalysisPage || $lfcAnalysisTitle->exists()) {
    $links['namespaces']['main']['text'] = 'Proposal';
    $links['namespaces']['lfcanalysis'] = [
     'class' => ($isAnalysisPage ? 'selected' : ''),
     'href' => ($isAnalysisPage ? $template->getTitle()->getLocalUrl() : $lfcAnalysisTitle->getLocalUrl()),
     'text' => 'LFC Analysis',
    ];
  }

  # Same as above, but with Evaluations
  if($isEvalPage || $evalTitle->exists()) {
    $links['namespaces']['main']['text'] = 'Proposal';
    $links['namespaces']['evaluations'] = [
     'class' => ($isEvalPage ? 'selected' : ''),
     'href' => ($isEvalPage ? $template->getTitle()->getLocalUrl() : $evalTitle->getLocalUrl()),
     'text' => 'Evaluations',
    ];
  }

  # Remove the talk tab, even if the talk page exists
  unset($links['namespaces']['talk']);
};
?>
