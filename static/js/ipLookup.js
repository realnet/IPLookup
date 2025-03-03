// 显示 IP 查询界面
function showIpLookup() {
    let content = `
        <h2>IP 查询</h2>
        <input type="text" id="ip_input" placeholder="请输入IP地址">
        <button onclick="lookupIP()">查询</button>

        <h3>EC2 实例信息</h3>
        <table id="ec2_table" class="hidden">
            <thead>
                <tr>
                    <th>云厂商</th><th>Region</th><th>类型</th><th>实例 ID</th><th>实例名称</th>
                    <th>私有 IP</th><th>公网 IP</th><th>实例类型</th><th>状态</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>

        <h3>VPC 信息</h3>
        <table id="vpc_table" class="hidden">
            <thead>
                <tr><th>Region</th><th>VPC ID</th><th>VPC 名称</th><th>子网 ID</th><th>子网 CIDR</th></tr>
            </thead>
            <tbody></tbody>
        </table>

        <h3>安全组信息</h3>
        <table id="sg_table" class="hidden">
            <thead>
                <tr><th>安全组 ID</th><th>安全组名称</th></tr>
            </thead>
            <tbody></tbody>
        </table>

        <h3>安全组规则</h3>
        <table id="sg_detail_table" class="hidden">
            <thead>
                <tr><th>安全组 ID</th><th>方向</th><th>协议</th><th>端口范围</th><th>来源</th><th>描述</th></tr>
            </thead>
            <tbody></tbody>
        </table>
    `;

    $("#main-content").html(content); // 插入到主内容区
}

// 执行 IP 查询
function lookupIP() {
    let ip = $("#ip_input").val().trim();
    if (!ip) {
        alert("请输入 IP 地址！");
        return;
    }

    $.get("/api/ip-lookup/?ip=" + ip, function(data) {
        console.log("API 返回数据:", data);

        if (!data || typeof data !== "object") {
            alert("查询失败: API 返回无效的数据格式");
            return;
        }

        // **1. 清空旧数据**
        $("#ec2_table tbody").empty();
        $("#vpc_table tbody").empty();
        $("#sg_table tbody").empty();
        $("#sg_detail_table tbody").empty();

        // **2. 显示表格**
        $("#ec2_table").removeClass("hidden");
        $("#vpc_table").removeClass("hidden");
        $("#sg_table").removeClass("hidden");
        $("#sg_detail_table").removeClass("hidden");

        // **3. 填充 EC2 信息**
        $("#ec2_table tbody").append(`
            <tr>
                <td>${data.cloud || ''}</td>
                <td>${data.region || ''}</td>
                <td>${data.type || ''}</td>
                <td>${data.instance_id || ''}</td>
                <td>${data.instance_name || ''}</td>
                <td>${data.private_ips ? data.private_ips.join(', ') : ''}</td>
                <td>${data.public_ips ? data.public_ips.join(', ') : ''}</td>
                <td>${data.instance_type || ''}</td>
                <td>${data.state || ''}</td>
            </tr>
        `);

        // **4. 填充 VPC 信息**
        $("#vpc_table tbody").append(`
            <tr>
                <td>${data.region || ''}</td>
                <td>${data.vpc_id || ''}</td>
                <td>${data.vpc_name || ''}</td>
                <td>${data.subnet_id || ''}</td>
                <td>${data.subnet_cidr || ''}</td>
            </tr>
        `);

        // **5. 填充安全组信息**
        if (Array.isArray(data.security_groups_detail)) {
            data.security_groups_detail.forEach(sg => {
                $("#sg_table tbody").append(`
                    <tr>
                        <td>${sg.group_id || ''}</td>
                        <td>${sg.group_name || ''}</td>
                    </tr>
                `);

                // **填充安全组入站规则**
                if (Array.isArray(sg.inbound_rules)) {
                    sg.inbound_rules.forEach(rule => {
                        $("#sg_detail_table tbody").append(`
                            <tr>
                                <td>${sg.group_id}</td>
                                <td>Inbound</td>
                                <td>${rule.ip_protocol || ''}</td>
                                <td>${rule.from_port || ''}-${rule.to_port || ''}</td>
                                <td>${rule.source || ''}</td>
                                <td>${rule.rule_description || ''}</td>
                            </tr>
                        `);
                    });
                }

                // **填充安全组出站规则**
                if (Array.isArray(sg.outbound_rules)) {
                    sg.outbound_rules.forEach(rule => {
                        $("#sg_detail_table tbody").append(`
                            <tr>
                                <td>${sg.group_id}</td>
                                <td>Outbound</td>
                                <td>${rule.ip_protocol || ''}</td>
                                <td>${rule.from_port || ''}-${rule.to_port || ''}</td>
                                <td>${rule.source || ''}</td>
                                <td>${rule.rule_description || ''}</td>
                            </tr>
                        `);
                    });
                }
            });
        }

    }).fail(function(xhr) {
        alert("查询失败：" + (xhr.responseJSON?.error || "未知错误"));
    });
}
