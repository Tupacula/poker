document.getElementById('fold').addEventListener('click', () => logAction('fold'));
document.getElementById('call').addEventListener('click', () => logAction('call'));
document.getElementById('raise').addEventListener('click', () => logAction('raise'));

function logAction(act) {
  const el = document.getElementById('log');
  const time = new Date().toLocaleTimeString();
  el.innerText = `${act.toUpperCase()} @ ${time}`;
}
