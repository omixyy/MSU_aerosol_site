function getBlockIndex(block) {
    const blocks = Array.from(block.parentElement.children);
    return blocks.indexOf(block);
}

function moveLeft(button) {
  const block = button.parentElement;
  const previousBlock = block.previousElementSibling;
  if (previousBlock && previousBlock.classList.contains('device_content')) {
    block.parentNode.insertBefore(block, previousBlock);
    const newIndex = getBlockIndex(block);
  }
}

function moveRight(button) {
  const block = button.parentElement;
  const nextBlock = block.nextElementSibling;
  if (nextBlock && nextBlock.classList.contains('device_content')) {
    block.parentNode.insertBefore(nextBlock, block);
    const newIndex = getBlockIndex(block);
  }
}

function activateEdit() {
  var additionalButtons = document.getElementsByClassName("btn btn-outline-dark hidden");
  for (let i = 0; i < additionalButtons.length; i++) {
    if (additionalButtons[i].style.display === 'none' || additionalButtons[i].style.display === "") {
      additionalButtons[i].style.display = 'inline';
    } else {
      additionalButtons[i].style.display = 'none';
    }
  }

  var editButtons = document.getElementsByClassName("btn btn-outline-success accept");
  for (let i = 0; i < editButtons.length; i++) {
    if (editButtons[i].style.display === 'none' || editButtons[i].style.display === "") {
      editButtons[i].style.display = 'inline-flex';
    } else {
      editButtons[i].style.display = 'none';
    }
  }
}

function sendOrderToServer() {
  const blocks = document.getElementsByClassName('device_content');
  const order = [];
  for (let i = 0; i < blocks.length; i++) {
    order.push(blocks[i].id.slice(3));
  }
  fetch('/update_index', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ order: order })
  })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
}
