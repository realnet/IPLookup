
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
          // 检查 col 是否有 render 函数
          if (col.render) {
            return `<td>${col.render(item)}</td>`;
          }
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


function showTasks() {
    const container = document.getElementById("main-content");
    container.innerHTML = "<h2>变更任务列表</h2><div id='task-list'></div>";
    loadTaskList();
}

function loadTaskList() {
    fetch('/api/aws/route53/tasks/')
        .then(res => res.json())
        .then(tasks => {
            let html = "<table><tr><th>Task ID</th><th>Status</th><th>操作</th></tr>";
            tasks.forEach(t => {
                html += `
                    <tr>
                        <td>${t.task_id}</td>
                        <td>${t.status}</td>
                        <td><button onclick="viewTaskDetail('${t.task_id}')">查看/确认</button></td>
                    </tr>
                `;
            });
            html += "</table>";
            document.getElementById("task-list").innerHTML = html;
        })
        .catch(err => console.error(err));
}

function viewTaskDetail(taskId) {
    fetch(`/api/aws/route53/tasks/${taskId}/`)
        .then(res => res.json())
        .then(task => {
            if (task.error) {
                alert("任务不存在");
                return;
            }
            const msg = `
            任务ID: ${task.task_id}\n
            状态: ${task.status}\n
            旧数据: ${JSON.stringify(task.old_data)}\n
            新数据: ${JSON.stringify(task.new_data)}\n
            `;
            if (confirm(msg + "\n确认执行变更?")) {
                // 需要 record_id
                const recordId = prompt("请输入记录ID (示例)"); // 或在task中存record_id
                applyTask(task.task_id, recordId);
            }
        })
        .catch(err => console.error(err));
}

function applyTask(taskId, recordId) {
    fetch(`/api/aws/route53/tasks/${taskId}/apply/`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ record_id: recordId })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        loadTaskList();
    })
    .catch(err => console.error(err));
}


function renderTable(title, tableId, columns, data) {
    const container = document.getElementById("main-content");
    container.innerHTML = `<h2>${title}</h2><table id="${tableId}" class="styled-table"></table>`;

    const table = document.getElementById(tableId);
    table.innerHTML = "";

    // 创建表头
    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");
    columns.forEach(col => {
        let th = document.createElement("th");
        th.textContent = col.header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // 创建表格内容
    let tbody = document.createElement("tbody");
    data.forEach(row => {
        let tr = document.createElement("tr");
        columns.forEach(col => {
            let td = document.createElement("td");
            // 如果 col 有 render 函数，则用它来生成单元格内容
            if (col.render) {
                td.innerHTML = col.render(row);
            } else {
                // 否则按 field 显示
                td.textContent = row[col.field] || "-";
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
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






