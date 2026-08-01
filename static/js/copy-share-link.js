(function () {
  document.addEventListener('click', function (event) {
    var btn = event.target.closest('[data-copy-target]');
    if (!btn) return;
    var input = document.getElementById(btn.getAttribute('data-copy-target'));
    if (!input) return;

    input.select();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(input.value);
    }

    var feedback = document.getElementById(btn.getAttribute('data-copy-feedback'));
    if (!feedback) return;
    feedback.classList.remove('opacity-0');
    clearTimeout(feedback._hideTimer);
    feedback._hideTimer = setTimeout(function () {
      feedback.classList.add('opacity-0');
    }, 2000);
  });
})();
