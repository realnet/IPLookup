/***********************
 * 通用：占位功能
 ***********************/
function showPlaceholder(name) {
  const content = document.getElementById('main-content');
  content.innerHTML = `
    <h2>${name}</h2>
    <p>该功能暂未开发。</p>
  `;
}

/***********************
 * 通用：表格搜索
 ***********************/
function filterTable(tableId, inputId) {
  const input = document.getElementById(inputId);
  const filter = input.value.toLowerCase();
  const table = document.getElementById(tableId);
  if(!table) return;
  const trs = table.getElementsByTagName('tr');
  for(let i = 1; i < trs.length; i++) {
    let tds = trs[i].getElementsByTagName('td');
    let show = false;
    for(let j = 0; j < tds.length; j++) {
      const txtValue = tds[j].textContent || tds[j].innerText;
      if(txtValue.toLowerCase().indexOf(filter) > -1) {
        show = true;
        break;
      }
    }
    trs[i].style.display = show ? '' : 'none';
  }
}
