document.addEventListener('DOMContentLoaded', function () {
  const links = document.querySelectorAll('a');
  const currentPath = window.location.pathname;

  links.forEach(link => {
    if (link.pathname === currentPath && !(link.className === 'dropdown-item')) {
      link.addEventListener('click', function (event) {
          event.preventDefault();
      });
    }
  });
});