document.querySelectorAll('.partner-upload input[type="file"]').forEach(function (input) {
  const status = input.parentElement.querySelector('.partner-upload__status');
  input.addEventListener('change', function () {
    status.textContent = Array.from(input.files, function (file) { return file.name; }).join(', ');
  });
});
