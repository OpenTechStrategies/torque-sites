<?php
$wgHooks['SkinTemplateNavigation'][] = function ( $template, &$links ) {
  $currentTitle = $template->getTitle()->getFullText();
  $lfc_prepend = "LFC Analysis of ";
  $eval_prepend = "Evaluations of ";

  $isAnalysisPage = (strlen($currentTitle) > strlen($lfc_prepend) && substr($currentTitle, 0, strlen($lfc_prepend)) === $lfc_prepend);
  $isEvalPage = (strlen($currentTitle) > strlen($eval_prepend) && substr($currentTitle, 0, strlen($eval_prepend)) === $eval_prepend);

  $originalPageTitle = $currentTitle;
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
  if($isAnalysisPage || $lfcAnalysisTitle->exists()) {
    $links['namespaces']['main']['text'] = 'Proposal';
    $links['namespaces']['lfcanalysis'] = [
     'class' => ($isAnalysisPage ? 'selected' : ''),
     'href' => ($isAnalysisPage ? $template->getTitle()->getLocalUrl() : $lfcAnalysisTitle->getLocalUrl()),
     'text' => 'LFC Analysis',
    ];
  }
  if($isEvalPage || $evalTitle->exists()) {
    $links['namespaces']['main']['text'] = 'Proposal';
    $links['namespaces']['evaluations'] = [
     'class' => ($isEvalPage ? 'selected' : ''),
     'href' => ($isEvalPage ? $template->getTitle()->getLocalUrl() : $evalTitle->getLocalUrl()),
     'text' => 'Evaluations',
    ];
  }

  unset($links['namespaces']['talk']);
};
?>
