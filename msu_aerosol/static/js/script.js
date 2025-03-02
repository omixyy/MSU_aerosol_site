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

function searchText() {
    const searchString = document.getElementById('searchInput').value.trim();
    if (!searchString) {
        alert('Введите текст для поиска');
        return;
    }
    const content = document.getElementsByClassName('default');
    const regex = new RegExp(`(${searchString})`, 'gi');
    const highlightedContent = content.replace(regex, '<mark>$1</mark>');
    document.getElementsByClassName('default').innerHTML = highlightedContent;
    const firstMatch = document.querySelector('mark');
    if (firstMatch) {
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}