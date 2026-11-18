/**
 * KM0 Digital — SOGo Angular Material theme (coherent dark)
 * Paper #0B1220 · Snow #141B28 · Mist #2A3344 · Ink #E6E9ED · Signal #2DD4BF
 *
 * SOGo uses palette shades directly via md-colors:
 *   background-200/300 → surfaces (must be dark)
 *   background-500/600/700 → ink/text (must be light)
 * Folder rows use md-background md-hue-1; message list uses md-content default.
 * Mounted as theme.js by Mailcow (data/conf/sogo/custom-theme.js).
 */
(function () {
  'use strict';
  angular.module('SOGo.Common')
    .config(configure);

  configure.$inject = ['$mdThemingProvider'];
  function configure($mdThemingProvider) {
    // Define full palette (avoid extendPalette leftover contrast maps from grey).
    $mdThemingProvider.definePalette('km0-paper', {
      '50': '141B28',   // Snow — light-theme md-content fallback
      '100': '1C2433',  // elevated surface
      '200': '141B28',  // empty-state / preview pane (md-colors background-200)
      '300': '0B1220',  // sidenav body (md-colors background-300)
      '400': '2A3344',  // Mist
      '500': 'E6E9ED',  // Ink — SOGo empty-state / secondary text via md-colors
      '600': 'C5CAD3',  // muted ink
      '700': 'E6E9ED',  // ink (calendar / captions via md-colors)
      '800': '0B1220',  // Paper — dark-theme folder row (md-hue-1)
      '900': '050A14',  // deepest
      '1000': 'E6E9ED',
      'A100': '2A3344', // Mist
      'A200': '141B28', // Snow
      'A400': '0B1220', // Paper — dark-theme md-content default
      'A700': '2DD4BF', // Signal (rare accent-on-paper)
      contrastDefaultColor: 'light',
      // Light ink shades: if used as a surface, prefer dark contrast text.
      contrastDarkColors: ['500', '600', '700', '1000', 'A700']
    });

    $mdThemingProvider.definePalette('km0-signal', {
      '50': 'F0FDFA',
      '100': 'CCFBF1',
      '200': '99F6E4',
      '300': '5EEAD4',
      '400': '2DD4BF',
      '500': '14B8A6',
      '600': '0F766E',  // top toolbars
      '700': '0D9488',  // sidenav profile toolbar (primary hue-2)
      '800': '0F766E',  // list toolbar in dark mode (accent hue-1)
      '900': '134E4A',
      'A100': '99F6E4',
      'A200': '2DD4BF',
      'A400': '5EEAD4',
      'A700': '0F766E',
      contrastDefaultColor: 'light',
      contrastDarkColors: ['50', '100', '200', '300', '400', 'A100', 'A200', 'A400']
    });

    $mdThemingProvider.theme('default')
      .primaryPalette('km0-signal', {
        'default': '600',  // top toolbars
        'hue-1': '400',
        'hue-2': '700',    // sidenav profile toolbar
        'hue-3': '800'
      })
      .accentPalette('km0-signal', {
        'default': '400',  // FAB / accents
        'hue-1': '800',    // center list toolbar (dark, not mint island)
        'hue-2': '400',    // selected message / current day
        'hue-3': 'A700'
      })
      .backgroundPalette('km0-paper', {
        'default': 'A400', // message list md-content
        'hue-1': '800',    // folder rows
        'hue-2': '900',
        'hue-3': 'A200'
      })
      .dark();

    $mdThemingProvider.generateThemesOnDemand(false);
  }
})();
