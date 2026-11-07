// Tell the server when a visitor closes a dismissible alert. Needs Bootstrap 5
// (for the close button); no jQuery.
document.addEventListener("click", function (event) {
  var button = event.target.closest(".user-alert .btn-close");
  if (!button) return;
  var alert = button.closest(".user-alert");
  var url = alert && alert.dataset.dismissUrl;
  if (!url) return;
  fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": alert.dataset.csrfToken || "" },
  }).catch(function (error) { console.warn("Alert dismissal not saved:", error); });
});
