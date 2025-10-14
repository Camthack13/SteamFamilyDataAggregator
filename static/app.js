// Hard-enforce max 5 selections
function updateFriendCheckboxes() {
  const boxes = Array.from(document.querySelectorAll('.friend-checkbox'));
  const checked = boxes.filter(b => b.checked);
  const limit = 5;
  const disabled = checked.length >= limit;
  boxes.forEach(b => { if (!b.checked) b.disabled = disabled; });
  const note = document.getElementById('limit-note');
  if (note) note.classList.toggle('hidden', !disabled);
}

document.addEventListener('change', (e) => {
  if (e.target && e.target.classList.contains('friend-checkbox')) {
    updateFriendCheckboxes();
  }
});

document.addEventListener('DOMContentLoaded', updateFriendCheckboxes);

document.addEventListener('click', (e) => {
  const modal = document.getElementById('modal');
  if (!modal || modal.classList.contains('hidden')) return;
  if (e.target === modal) modal.classList.add('hidden');
});

// Simple client-side table sort + filter
let sortState = { key: 'family_playtime_forever_h', dir: 'desc' };

function sortTable(th) {
  const table = document.getElementById('results');
  const key = th.getAttribute('data-key');
  const type = th.getAttribute('data-type') || 'str';
  const dir = (th.classList.contains('sorted') && th.classList.contains('asc')) ? 'desc' : 'asc';
  sortState = { key, dir };
  table.querySelectorAll('th').forEach(h => h.classList.remove('sorted', 'asc', 'desc'));
  th.classList.add('sorted', dir);

  const rows = Array.from(table.querySelectorAll('tbody tr'));
  const idx = Array.from(table.querySelectorAll('thead th')).indexOf(th);
  rows.sort((a, b) => {
    let va = a.children[idx].innerText.trim();
    let vb = b.children[idx].innerText.trim();
    if (type === 'num') { va = parseFloat(va) || 0; vb = parseFloat(vb) || 0; }
    else { va = va.toLowerCase(); vb = vb.toLowerCase(); }
    if (va < vb) return dir === 'asc' ? -1 : 1;
    if (va > vb) return dir === 'asc' ? 1 : -1;
    return 0;
  });
  const tbody = table.querySelector('tbody');
  rows.forEach(r => tbody.appendChild(r));
}

function filterTable() {
  const q = (document.getElementById('filter').value || '').toLowerCase();
  const rows = Array.from(document.querySelectorAll('#results tbody tr'));
  rows.forEach(tr => {
    const appid = tr.children[0].innerText.toLowerCase();
    const name = tr.children[1].innerText.toLowerCase();
    tr.style.display = (appid.includes(q) || name.includes(q)) ? '' : 'none';
  });
}