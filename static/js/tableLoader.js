/***********************
 * 通用：加载表格
 ***********************/
function loadDataTable(apiEndpoint, title, tableId, columns) {
  if (!columns || !Array.isArray(columns)) {
    console.error(`错误: ${title} 的 columns 未定义或不是数组`, columns);
    return;
  }

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

// 定义 EIP 表格列
const eipColumns = [
    { header: "名称", field: "name" },
    { header: "公网 IP", field: "allocated_ipv4_address" },
    { header: "类型", field: "type" },
    { header: "分配 ID", field: "allocation_id" },
    { header: "反向 DNS", field: "reverse_dns_record" },
    { header: "绑定实例 ID", field: "associated_instance_id" },
    { header: "私有 IP", field: "private_ip_address" },
    { header: "关联 ID", field: "association_id" },
    { header: "网卡拥有者 ID", field: "network_interface_owner_account_id" },
    { header: "边界组", field: "network_border_group" }
];


console.log("EIP Columns Loaded:", eipColumns);

// 定义 VPC Endpoint 表格列
const vpcEndpointColumns = [
    { header: "名称", field: "name" },
    { header: "VPC Endpoint ID", field: "endpoint_id" },
    { header: "类型", field: "endpoint_type" },
    { header: "状态", field: "status" },
    { header: "服务名称", field: "service_name" },
    { header: "VPC ID", field: "vpc_id" },
    { header: "创建时间", field: "creation_time" },
    { header: "网卡 ID", field: "network_interfaces" },
    { header: "子网 ID", field: "subnets" }
];

console.log("VPC Endpoint Columns Loaded:", vpcEndpointColumns);

// 定义 Route 53 记录表格列
const route53Columns = [
    { header: "记录名称", field: "record_name" },
    { header: "类型", field: "record_type" },
    { header: "路由策略", field: "routing_policy" },
    { header: "别名", field: "alias" },
    { header: "值 / 路由流量到", field: "value" },
    { header: "TTL", field: "ttl" }
];

console.log("Route 53 Columns Loaded:", route53Columns);



