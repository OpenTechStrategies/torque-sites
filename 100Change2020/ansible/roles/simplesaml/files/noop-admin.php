<?php

  /*
   * Installing this file in simplesaml, and then referencing it
   * effectively disables the UI when combined with setting
   * the admin.protectindexpage config to true.  All the UI pages
   * will force an attempt to log in as admin, which will get
   * delegated to here.
   *
   * For now, we just return 403 forbidden, but that could be changed
   * to something more eloquent if needed.
   */

  class NoopAdmin extends \SimpleSAML\Auth\Source {
    public function authenticate(&$state) {
      http_response_code(403);
      exit();
    }
  }

  $config['admin'] = ["NoopAdmin"];
?>
