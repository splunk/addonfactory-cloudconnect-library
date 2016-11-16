module.exports = function(grunt) {
    'use strict';

    var buildinfo = grunt.file.readJSON('build.json');
    buildinfo.buildNumber = process.env['BUILDNUMBER'] || 0;

    var re = /Splunk_TA_.*/;
    if (buildinfo.name.match(re)) {
        buildinfo.type = "TA";
    }

    require('time-grunt')(grunt);

    require('ext-grunt-horde')
      .create(grunt)
      .demand('initConfig.buildinfo', buildinfo)
      .loot('ext-grunt-basebuild')
      .attack();
};
