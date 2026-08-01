(function () {
  function syncFromLabel(input, hidden, datalist) {
    var options = datalist.querySelectorAll('option');
    for (var i = 0; i < options.length; i++) {
      if (options[i].value === input.value) {
        hidden.value = options[i].getAttribute('data-key');
        return true;
      }
    }
    return false;
  }

  function revertToLastValid(input, hidden, datalist) {
    var current = datalist.querySelector('option[data-key="' + hidden.value + '"]');
    input.value = current ? current.value : '';
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-species-search]').forEach(function (input) {
      var hidden = document.getElementById(input.getAttribute('data-target'));
      var datalist = document.getElementById(input.getAttribute('list'));
      if (!hidden || !datalist) return;

      input.addEventListener('change', function () {
        syncFromLabel(input, hidden, datalist);
      });
      input.addEventListener('blur', function () {
        if (!syncFromLabel(input, hidden, datalist)) {
          revertToLastValid(input, hidden, datalist);
        }
      });
    });
  });
})();
