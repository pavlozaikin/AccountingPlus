(function () {
  function setHeights() {
    var header = document.getElementById('siteHeader');
    var footer = document.getElementById('siteFooter');
    var root = document.documentElement;
    root.style.setProperty('--header-h', header ? header.offsetHeight + 'px' : '0px');
    root.style.setProperty('--footer-h', footer ? footer.offsetHeight + 'px' : '0px');
  }
  window.addEventListener('load', setHeights);
  window.addEventListener('resize', setHeights);
})();
