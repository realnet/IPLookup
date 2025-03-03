/***********************
 * 通用：加载表格
 ***********************/
function loadDataTable(apiEndpoint, title, tableId, columns) {
  const content = document.getElementById('main-content');
  content.innerHTML = `
    <h2>${title}</h2>
    <div class="search-container">
      <label>搜索: </label>
      <input type="text" id="search-input" placeholder="输入关键字...">
    </div>
    <table id="${tableId}">
      <thead>
        <tr>
          ${columns.map(col => `<th>${col.header}</th>`).join('')}
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  `;

  fetch(apiEndpoint)
    .then(res => res.json())
    .then(data => {
      const tbody = document.querySelector(`#${tableId} tbody`);
      tbody.innerHTML = '';
      data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = columns.map(col => {
          const val = item[col.field] || '';
          return `<td>${val}</td>`;
        }).join('');
        tbody.appendChild(tr);
      });
    })
    .catch(err => console.error(err));

  const searchInput = document.getElementById('search-input');
  searchInput.addEventListener('keyup', function() {
    filterTable(tableId, 'search-input');
  });
}

/***********************
 * 各资源列配置
 ***********************/
const ec2Columns = [
  { header: 'Instance ID', field: 'instance_id' },
  { header: 'Name',        field: 'name' },
  { header: 'Private IPs', field: 'private_ips' },
  { header: 'Public IPs',  field: 'public_ips' },
  { header: 'VPC ID',      field: 'vpc_id' },
  { header: 'Subnet ID',   field: 'subnet_id' },
  { header: 'Instance Type', field: 'instance_type' },
  { header: 'State',       field: 'state' },
  { header: 'Region',      field: 'region' },
];

const vpcColumns = [
  { header: 'VPC ID',    field: 'vpc_id' },
  { header: 'Name',      field: 'name' },
  { header: 'IPv4 CIDR', field: 'ipv4_cidr' },
  { header: 'Owner ID',  field: 'owner_id' },
  { header: 'Region',    field: 'region' },
];

const routeColumns = [
  { header: 'Route Table ID', field: 'route_table_id' },
  { header: 'Name',           field: 'name' },
  { header: 'VPC',            field: 'vpc' },
  { header: 'Region',         field: 'region' },
];

const sgColumns = [
  { header: 'Group ID',            field: 'group_id' },
  { header: 'Group Name',          field: 'group_name' },
  { header: 'VPC ID',              field: 'vpc_id' },
  { header: 'Description',         field: 'description' },
  { header: 'Owner',               field: 'owner' },
  { header: 'Inbound #',           field: 'inbound_rules_count' },
  { header: 'Outbound #',          field: 'outbound_rules_count' },
];
