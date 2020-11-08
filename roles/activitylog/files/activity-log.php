<?php
wfLoadExtension('ActivityLog');
$wgMessagesDirs['ActivityLogConfiguration'] = 'ActivityLogConfiguration/i18n';
$wgActivityLogHooksToWatch["ArticleViewHeader"] = function ($article) {
  $referrer = $_SERVER['HTTP_REFERER'];
  $ourServer = "http://torque.leverforchange.org";

  if($referrer && $ourServer == substr($referrer, 0, strlen($ourServer))) {
    return array($article->getContext()->getUser(),
      $article->getTitle(),
      "activitylog-articleviewheader-with-referrer",
      $_SERVER['HTTP_REFERER']
    );
  } else {
    return array($article->getContext()->getUser(),
      $article->getTitle(),
      "activitylog-articleviewheader"
    );
  }
};

$wgActivityLogHooksToWatch["UserLoginComplete"] = function(&$user, &$inject_html, $direct) {
  global $wgTitle;
  return array($user, $wgTitle, "activitylog-userlogin");
};

$wgActivityLogHooksToWatch["PageContentSave"] = function($wikiPage, $user, $content, &$summary, $isMinor, $isWatch, $section, $flags, $status) {
  return array($user, $wikiPage->getTitle(), "activitylog-articlesavepage");
};
?>
