// route53.js
function editRoute53Record(recordId) {
    console.log('editRoute53Record function called with recordId:', recordId);
    // 显示模态框
    $('#edit-modal').css('display', 'block');
    console.log('Modal display style after setting:', $('#edit-modal').css('display'));

    // 获取记录信息并填充到模态框中
    fetch(`/api/aws/route53/${recordId}/`)
      .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
      .then(data => {
            $('#record-id').val(recordId);
            $('#record-name').val(data.record_name);
            $('#record-type').val(data.record_type);
            $('#routing-policy').val(data.routing_policy);

            // 处理 value 字段，将字符串化的数组转换为数组
            let valueArray;
            try {
                valueArray = JSON.parse(data.value);
            } catch (error) {
                valueArray = [data.value];
            }
            $('#record-value').val(valueArray.join(','));

            $('#ttl').val(data.ttl);
        })
      .catch(err => {
            console.error('Fetch error:', err);
            alert('An error occurred while fetching the record. Please try again.');
            // 关闭模态框
            $('#edit-modal').css('display', 'none');
        });
}

function deleteRoute53Record(recordId) {
    alert("TODO: 实现删除逻辑");
}

// 定义 Route 53 记录表格列
const route53Columns = [
    { header: "记录名称", field: "record_name" },
    { header: "类型", field: "record_type" },
    { header: "路由策略", field: "routing_policy" },
    { header: "别名", field: "alias" },
    { header: "值 / 路由流量到", field: "value" },
    { header: "TTL", field: "ttl" },
    { header: "操作",
        render: (rowData) => {
            const editButton = `<button class="blue-button" onclick="editRoute53Record(${rowData.id})">EDIT</button>`;
            const deleteButton = `<button class="red-button" onclick="deleteRoute53Record(${rowData.id})">DELETE</button>`;
            console.log('Edit button HTML:', editButton);
            console.log('Delete button HTML:', deleteButton);
            return editButton + deleteButton;
        }
    }
];

console.log("Route 53 Columns Loaded:", route53Columns);


