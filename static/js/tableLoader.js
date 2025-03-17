function loadDataTable(apiEndpoint, title, tableId, columns) {
  // In-memory data
  let allData = [];
  let currentPage = 1;
  let pageSize = 10;

  // 1) Clear #main-content and insert a fresh table container
  const content = document.getElementById('main-content');
  content.innerHTML = `
    <h2>${title}</h2>
    <div class="search-container" style="margin-bottom:10px;">
      <label style="font-weight:bold;margin-right:8px;">Search:</label>
      <input type="text" id="search-input" placeholder="Enter keywords..." 
             style="padding:4px;font-size:14px;border:1px solid #ccc;border-radius:4px;">
    </div>
    <table id="${tableId}" border="1" style="width:100%; border-collapse:collapse;">
      <thead>
        <tr>
          ${columns.map(col => `<th style="padding:6px 8px;background:#f0f0f0;">${col.header}</th>`).join('')}
        </tr>
      </thead>
      <tbody id="${tableId}-tbody"></tbody>
    </table>
    <div id="${tableId}-pagination" style="margin-top:10px; text-align:center;"></div>
  `;

  // 2) Fetch data from API
  fetch(apiEndpoint)
    .then(res => res.json())
    .then(data => {
      console.log('API response data:', data);
      if (Array.isArray(data)) {
        allData = data;
        currentPage = 1;
        renderTable();
      } else {
        console.error('API response is not an array:', data);
        // Optional: show an error row
        const tableBody = document.getElementById(`${tableId}-tbody`);
        tableBody.innerHTML = `<tr><td colspan="${columns.length}">Error: Data is not an array</td></tr>`;
      }
    })
    .catch(err => {
      console.error('Fetch error:', err);
      const tableBody = document.getElementById(`${tableId}-tbody`);
      tableBody.innerHTML = `<tr><td colspan="${columns.length}">Fetch error: ${err}</td></tr>`;
    });

  // 3) Search event
  const searchInput = document.getElementById('search-input');
  searchInput.addEventListener('keyup', function() {
    currentPage = 1;
    renderTable();
  });

  /**
   * Renders table with search + pagination
   */
  function renderTable() {
    const tableBody = document.getElementById(`${tableId}-tbody`);
    tableBody.innerHTML = '';

    // 1) Filter by search
    const filteredData = applySearch(allData);

    // 2) Paginate
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    const paginatedData = filteredData.slice(start, end);

    // 3) Render rows
    if (paginatedData.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="${columns.length}">No data</td></tr>`;
    } else {
      paginatedData.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = columns.map(col => {
          if (col.render) {
            return `<td style="padding:6px 8px;">${col.render(item)}</td>`;
          }
          const val = item[col.field] || '';
          return `<td style="padding:6px 8px;">${val}</td>`;
        }).join('');
        tableBody.appendChild(tr);
      });
    }

    // 4) Update pagination
    updatePagination(filteredData.length);
  }

  /**
   * Filters data by search
   */
  function applySearch(data) {
    const val = (searchInput.value || '').trim().toLowerCase();
    if (!val) return data;
    return data.filter(item => {
      return columns.some(col => {
        const fieldVal = item[col.field];
        if (!fieldVal) return false;
        return fieldVal.toString().toLowerCase().includes(val);
      });
    });
  }

  /**
   * Creates pagination controls (beautified with inline styles)
   */
  function updatePagination(filteredCount) {
    const paginationContainer = document.getElementById(`${tableId}-pagination`);
    paginationContainer.innerHTML = '';

    if (filteredCount === 0) {
      paginationContainer.innerHTML = '<p>No data</p>';
      return;
    }

    const totalPages = Math.ceil(filteredCount / pageSize);

    // Some inline styling for the buttons and select
    let html = `
      <button 
        id="${tableId}-prev-page" 
        style="padding:6px 12px;font-size:14px;margin-right:8px;background-color:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;"
        ${currentPage === 1 ? 'disabled style="background-color:#ccc;cursor:not-allowed;"' : ''}>
        Prev
      </button>

      <span style="font-size:14px;">
        Page ${currentPage} / ${totalPages}
      </span>

      <button 
        id="${tableId}-next-page" 
        style="padding:6px 12px;font-size:14px;margin-left:8px;background-color:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;"
        ${currentPage === totalPages ? 'disabled style="background-color:#ccc;cursor:not-allowed;"' : ''}>
        Next
      </button>

      <select 
        id="${tableId}-page-size" 
        style="padding:4px;font-size:14px;margin-left:10px;border-radius:4px;border:1px solid #ccc;">
        <option value="10"  ${pageSize === 10  ? 'selected' : ''}>10</option>
        <option value="20"  ${pageSize === 20  ? 'selected' : ''}>20</option>
        <option value="50"  ${pageSize === 50  ? 'selected' : ''}>50</option>
        <option value="100" ${pageSize === 100 ? 'selected' : ''}>100</option>
      </select>
    `;
    paginationContainer.innerHTML = html;

    // Prev
    document.getElementById(`${tableId}-prev-page`).addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        renderTable();
      }
    });

    // Next
    document.getElementById(`${tableId}-next-page`).addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        renderTable();
      }
    });

    // Page size
    document.getElementById(`${tableId}-page-size`).addEventListener('change', e => {
      pageSize = parseInt(e.target.value);
      currentPage = 1;
      renderTable();
    });
  }
}


/*******************************************************
 * The rest of your code for tasks, etc.
 *******************************************************/
function showTasks() {
  const container = document.getElementById("main-content");
  container.innerHTML = "<h2>Change Task List</h2><div id='task-list'></div>";
  loadTaskList();
}

function loadTaskList() {
  fetch('/api/aws/route53/tasks/')
    .then(res => res.json())
    .then(tasks => {
      let html = "<table><tr><th>Task ID</th><th>Status</th><th>Action</th></tr>";
      tasks.forEach(t => {
        html += `
          <tr>
            <td>${t.task_id}</td>
            <td>${t.status}</td>
            <td><button onclick="viewTaskDetail('${t.task_id}')">View/Confirm</button></td>
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
        alert("Task does not exist");
        return;
      }
      const msg = `
        Task ID: ${task.task_id}\n
        Status: ${task.status}\n
        Old data: ${JSON.stringify(task.old_data)}\n
        New data: ${JSON.stringify(task.new_data)}\n
      `;
      if (confirm(msg + "\nConfirm to proceed?")) {
        const recordId = prompt("Please enter record ID (example)");
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

/************************
 * Resource column config
 ************************/
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

// EIP columns
const eipColumns = [
    { header: "Name", field: "name" },
    { header: "Public IP", field: "allocated_ipv4_address" },
    { header: "Type", field: "type" },
    { header: "Allocation ID", field: "allocation_id" },
    { header: "Reverse DNS", field: "reverse_dns_record" },
    { header: "Associated Instance ID", field: "associated_instance_id" },
    { header: "Private IP", field: "private_ip_address" },
    { header: "Association ID", field: "association_id" },
    { header: "Network Interface Owner Account ID", field: "network_interface_owner_account_id" },
    { header: "Network Border Group", field: "network_border_group" }
];
console.log("EIP Columns Loaded:", eipColumns);

// VPC Endpoint columns
const vpcEndpointColumns = [
    { header: "Name", field: "name" },
    { header: "VPC Endpoint ID", field: "endpoint_id" },
    { header: "Type", field: "endpoint_type" },
    { header: "Status", field: "status" },
    { header: "Service Name", field: "service_name" },
    { header: "VPC ID", field: "vpc_id" },
    { header: "Creation Time", field: "creation_time" },
    { header: "Network Interfaces", field: "network_interfaces" },
    { header: "Subnets", field: "subnets" }
];
console.log("VPC Endpoint Columns Loaded:", vpcEndpointColumns);

// Load balancers columns
const awslbColumns = [
    { header: "Name", field: "name" },
    { header: "DNS name", field: "dns_name" },
    { header: "State", field: "state" },
    { header: "VPC ID", field: "vpc_id" },
    { header: "Availability Zone", field: "availability_zone" },
    { header: "Type", field: "type" }
];
console.log("lbColumns definition completed", awslbColumns);

// Listener rules columns
const awslrColumns = [
    { header: "Load Balancer", field: "load_balancer_name" },
    { header: "Protocal & Port", field: "protocol_port" },
    { header: "Security policy", field: "security_policy" },
    { header: "Default SSL/TLS", field: "default_ssl_tls" },
    { header: "Default Action", field: "forward_target_group" },
    { header: "Response Body", field: "response_body" },
    { header: "Response Code", field: "response_code" },
    { header: "Response Content Type", field: "response_content_type" }
];

// Target groups columns
const awstgColumns = [
    { header: "Name", field: "name" },
    { header: "Port", field: "port" },
    { header: "Protocol", field: "protocol" },
    { header: "Target type", field: "target_type" },
    { header: "Load balancer", field: "load_balancer_name" },
    { header: "VPC ID", field: "vpc_id" },
];


// 定义 WAF Rule Groups 的列
const wafrgColumns = [
  { header: "Name", field: "name" },
  { header: "RuleGroup ID", field: "rule_group_id" },
  { header: "Scope", field: "scope" },
  { header: "Capacity", field: "capacity" },
  { header: "Region", field: "region" },
  {
    header: "Rules",
    // 使用 render 函数, 将 rule_group 下的 rules 显示出来
    render: (item) => {
      if (!item.rules || item.rules.length === 0) {
        return "No rules";
      }
      // 逐条列出, 展示 name/priority/action, 或更多
      return item.rules.map(rule => {
        return `
          <div>
            <strong>${rule.name}</strong>
            (priority=${rule.priority}, action=${rule.action})
          </div>
        `;
      }).join('');
    }
  }
];

console.log("tableLoader.js is loaded");
