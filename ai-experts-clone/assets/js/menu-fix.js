/**
 * Standalone menu fix for local static clone.
 * Uses event delegation from document so it works even if the Impreza
 * theme JS crashes during initialization (e.g. usContentCarousel error).
 */
(function () {
  // Event delegation — fires for any click anywhere on the page
  document.addEventListener('click', function (e) {
    var control = e.target.closest('.w-nav-control');
    if (control) {
      e.preventDefault();
      var isOpen = control.classList.contains('active');
      if (isOpen) {
        control.classList.remove('active');
        document.documentElement.classList.remove('w-nav-open');
      } else {
        control.classList.add('active');
        document.documentElement.classList.add('w-nav-open');
      }
      return;
    }

    // Close button inside the overlay menu
    var closeBtn = e.target.closest('.w-nav-close');
    if (closeBtn) {
      e.preventDefault();
      var nav = closeBtn.closest('.w-nav');
      var ctrl = nav && nav.querySelector('.w-nav-control');
      if (ctrl) ctrl.classList.remove('active');
      document.documentElement.classList.remove('w-nav-open');
      return;
    }

    // Submenu arrows / anchors with children — toggle level_2 list
    var anchor = e.target.closest('.w-nav-anchor.level_1');
    if (anchor) {
      var li = anchor.closest('li.menu-item-has-children');
      var ctrl2 = document.querySelector('.w-nav-control');
      // Only intercept when the fullscreen menu is open
      if (li && ctrl2 && ctrl2.classList.contains('active')) {
        e.preventDefault();
        li.classList.toggle('us-open');
        var sub = li.querySelector('.w-nav-list.level_2');
        if (sub) {
          sub.style.display = li.classList.contains('us-open') ? 'block' : '';
        }
      }
    }
  }, true); // capture phase so we fire before theme JS
})();
