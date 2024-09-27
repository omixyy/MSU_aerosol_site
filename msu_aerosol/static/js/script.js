document.addEventListener('DOMContentLoaded', function () {
  const links = document.querySelectorAll('a');
  const currentHref = window.location.href;
  links.forEach(link => {
    if (link.href === currentHref && !(link.className === 'dropdown-item')) {
      link.addEventListener('click', function (event) {
          event.preventDefault();
      });
    }
  });
});