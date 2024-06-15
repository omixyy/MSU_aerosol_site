function getBlockIndex(block) {
    const blocks = Array.from(block.parentElement.children);
    return blocks.indexOf(block);
}

function moveLeft(button, complex_id) {
  const block = button.parentElement;
  const previousBlock = block.previousElementSibling;
  if (previousBlock && previousBlock.classList.contains('device_content')) {
    block.parentNode.insertBefore(block, previousBlock);
    const newIndex = getBlockIndex(block);
  }
}

function moveRight(button, complex_id) {
  const block = button.parentElement;
  const nextBlock = block.nextElementSibling;
  if (nextBlock && nextBlock.classList.contains('device_content')) {
    block.parentNode.insertBefore(nextBlock, block);
    const newIndex = getBlockIndex(block);
  }
}

function activateEdit(complex_id) {
  var additionalButtons = document.getElementsByClassName("btn btn-outline-dark hidden");
  for (let i = 0; i < additionalButtons.length; i++) {
    if (additionalButtons[i].style.display === 'none' || additionalButtons[i].style.display === "") {
      additionalButtons[i].style.display = 'inline';
    } else {
      additionalButtons[i].style.display = 'none';
    }
  }

  var editButton = document.getElementsByClassName("btn btn-outline-success accept")[0];
  if (editButton.style.display === 'none' || editButton.style.display === "") {
      editButton.style.display = 'inline-flex';
    } else {
      editButton.style.display = 'none';
    }
}
