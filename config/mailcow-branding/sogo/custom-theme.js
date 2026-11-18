/**
 * KM0 Digital — SOGo Angular Material theme
 * Paper #0B1220 · Snow #141B28 · Mist #2A3344 · Ink #E6E9ED · Signal #2DD4BF
 * Mounted as theme.js by Mailcow (data/conf/sogo/custom-theme.js).
 */
(function () {
  'use strict';
  angular.module('SOGo.Common')
    .config(configure);

  configure.$inject = ['$mdThemingProvider'];
  function configure($mdThemingProvider) {
    var paperGrey = $mdThemingProvider.extendPalette('grey', {
      '50': 'E6E9ED',
      '100': '2A3344',
      '200': '1C2433',
      '300': '141B28',
      '400': '141B28',
      '500': '0B1220',
      '600': '0B1220',
      '700': '0B1220',
      '800': '0B1220',
      '900': '0B1220',
      '1000': 'E6E9ED',
      'A100': '2A3344',
      'A200': '141B28',
      'A400': '0B1220',
      'A700': '0B1220',
      contrastDefaultColor: 'light'
    });

    var signalTeal = $mdThemingProvider.extendPalette('teal', {
      '300': '5EEAD4',
      '400': '2DD4BF',
      '500': '14B8A6',
      '600': '0F766E',
      '700': '0D9488',
      '800': '0F766E',
      'A200': '2DD4BF',
      'A400': '5EEAD4',
      'A700': '0F766E',
      contrastDefaultColor: 'dark',
      contrastDarkColors: ['300', '400', 'A200', 'A400']
    });

    $mdThemingProvider.definePalette('km0-paper', paperGrey);
    $mdThemingProvider.definePalette('km0-signal', signalTeal);

    $mdThemingProvider.theme('default')
      .primaryPalette('km0-signal', {
        'default': '600',
        'hue-1': '400',
        'hue-2': '700',
        'hue-3': '800'
      })
      .accentPalette('km0-signal', {
        'default': '400',
        'hue-1': '300',
        'hue-2': '600',
        'hue-3': 'A700'
      })
      .backgroundPalette('km0-paper')
      .dark();

    $mdThemingProvider.generateThemesOnDemand(false);
  }
})();
