$(document).ready(function() {
  $('#colorPicker').on('input', function() {
    var color = $(this).val();
    $('#selectedColorDisplay').css('background-color', color);
    $('#selectedColorHex').text('HEX: ' + color);
  });
});