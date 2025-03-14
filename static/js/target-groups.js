$(document).ready(function () {
    let allTargetGroups = [];
    let currentPage = 1;
    let pageSize = 10;

    // 点击菜单项加载 Target Groups
    $("#menu-target-groups").click(function (e) {
        e.preventDefault();
        showTargetGroupsPage();  // 在 #main-content 中插入/重建页面
        loadTargetGroups();      // 加载数据
    });

    /**
     * 在 #main-content 中插入一个新的 “Target Groups” 页面容器
     * 以便不与其他页面内容堆叠。
     */
    function showTargetGroupsPage() {
        // 1. 清空 main-content
        const mainContent = $("#main-content");
        if (mainContent.length === 0) {
            console.error("未找到 #main-content，无法插入 Target Groups 页面。");
            return;
        }
        mainContent.empty(); // 移除之前的内容（例如其他页面）

        // 2. 插入 Target Groups 容器
        mainContent.append(`
            <div id="target-groups-page">
                <h2>Target Groups</h2>
                <table id="tg-table" class="tg-table" border="1" style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr>
                            <th style="padding:6px 8px;background:#f0f0f0;">Target Group Name</th>
                            <th style="padding:6px 8px;background:#f0f0f0;">Protocol</th>
                            <th style="padding:6px 8px;background:#f0f0f0;">Port</th>
                            <th style="padding:6px 8px;background:#f0f0f0;">Target Type</th>
                            <th style="padding:6px 8px;background:#f0f0f0;">VPC ID</th>
                            <th style="padding:6px 8px;background:#f0f0f0;">Load Balancer</th>
                        </tr>
                    </thead>
                    <tbody id="tg-table-body">
                        <!-- JS 动态填充 -->
                    </tbody>
                </table>
                <div id="pagination-container" style="margin-top:10px; text-align:center;"></div>

                <!-- 详情容器 -->
                <div id="tg-detail-container" style="margin-top:20px; border:1px solid #ccc; padding:10px; display:none;">
                </div>
            </div>
        `);
    }

    /**
     * AJAX 加载 Target Groups 数据
     */
    function loadTargetGroups() {
        console.log("开始加载 Target Groups 数据...");

        $.ajax({
            url: "/api/aws/target-groups/",
            method: "GET",
            dataType: "json",
            success: function (data) {
                console.log("loadTargetGroups => ", data);

                if (!Array.isArray(data)) {
                    console.error("API 返回的数据格式错误:", data);
                    $("#tg-table-body").html("<tr><td colspan='6'>数据加载失败，请检查 API 响应</td></tr>");
                    return;
                }

                allTargetGroups = data;
                currentPage = 1;
                renderTable();
            },
            error: function (xhr, status, error) {
                console.error("请求 Target Groups 失败:", status, error);
                $("#tg-table-body").html("<tr><td colspan='6'>加载失败，请检查网络或 API</td></tr>");
            }
        });
    }

    /**
     * 渲染表格 + 分页
     */
    function renderTable() {
        const tableBody = $("#tg-table-body");
        tableBody.empty();

        if (allTargetGroups.length === 0) {
            tableBody.append("<tr><td colspan='6'>暂无数据</td></tr>");
            updatePagination();
            return;
        }

        // 分页
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        const paginatedData = allTargetGroups.slice(start, end);

        // 填充
        paginatedData.forEach(tg => {
            const row = `
                <tr data-id="${tg.id}">
                    <td class="tg-name" style="cursor:pointer;color:#09853c;text-decoration:underline;padding:6px 8px;">
                        ${tg.name}
                    </td>
                    <td style="padding:6px 8px;">${tg.protocol}</td>
                    <td style="padding:6px 8px;">${tg.port}</td>
                    <td style="padding:6px 8px;">${tg.target_type}</td>
                    <td style="padding:6px 8px;">${tg.vpc_id}</td>
                    <td style="padding:6px 8px;">${tg.load_balancer_name || 'N/A'}</td>
                </tr>
            `;
            tableBody.append(row);
        });

        // 点击行 => 加载详情
        $(".tg-name").off("click").on("click", function () {
            const tgId = $(this).closest("tr").data("id");
            loadTargetGroupDetail(tgId);
        });

        updatePagination();
    }

    /**
     * 美化分页控件
     */
    function updatePagination() {
        const paginationContainer = $("#pagination-container");
        paginationContainer.empty();

        if (allTargetGroups.length === 0) {
            paginationContainer.append("<p>暂无数据</p>");
            return;
        }

        const totalPages = Math.ceil(allTargetGroups.length / pageSize);

        // 使用内联样式美化按钮和下拉框
        let paginationHtml = `
            <button 
                id="prev-page" 
                style="padding:6px 12px;font-size:14px;margin-right:8px;background-color:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;"
                ${currentPage === 1 ? "disabled style='background-color:#ccc;cursor:not-allowed;'" : ""}
            >
                Prev
            </button>

            <span style="font-size:14px;">
                Page ${currentPage}/${totalPages}
            </span>

            <button 
                id="next-page" 
                style="padding:6px 12px;font-size:14px;margin-left:8px;background-color:#007bff;color:#fff;border:none;border-radius:4px;cursor:pointer;"
                ${currentPage === totalPages ? "disabled style='background-color:#ccc;cursor:not-allowed;'" : ""}
            >
                Next
            </button>

            <select 
                id="page-size-select"
                style="padding:4px;font-size:14px;margin-left:10px;border-radius:4px;border:1px solid #ccc;"
            >
                <option value="10"  ${pageSize === 10  ? "selected" : ""}>10</option>
                <option value="20"  ${pageSize === 20  ? "selected" : ""}>20</option>
                <option value="50"  ${pageSize === 50  ? "selected" : ""}>50</option>
                <option value="100" ${pageSize === 100 ? "selected" : ""}>100</option>
            </select>
        `;
        paginationContainer.append(paginationHtml);

        // 上一页
        $("#prev-page").off("click").on("click", function() {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });

        // 下一页
        $("#next-page").off("click").on("click", function() {
            if (currentPage < totalPages) {
                currentPage++;
                renderTable();
            }
        });

        // 切换每页数量
        $("#page-size-select").off("change").on("change", function() {
            pageSize = parseInt($(this).val());
            currentPage = 1;
            renderTable();
        });
    }

    /**
     * 加载 Target Group 详情
     */
    function loadTargetGroupDetail(tgId) {
        $.ajax({
            url: `/api/aws/target-groups/${tgId}/`,
            method: "GET",
            dataType: "json",
            success: function (tg) {
                console.log("loadTargetGroupDetail => ", tg);
                if (!tg || typeof tg !== "object") {
                    console.error("API 详情数据格式错误:", tg);
                    $("#tg-detail-container").html("<p>无法加载详情，请检查 API 响应</p>").show();
                    return;
                }

                // 显示基本信息
                let detailHtml = `
                    <h3>Target Group 详情</h3>
                    <p><strong>名称:</strong> ${tg.name}</p>
                    <p><strong>协议:</strong> ${tg.protocol}</p>
                    <p><strong>端口:</strong> ${tg.port}</p>
                    <p><strong>目标类型:</strong> ${tg.target_type}</p>
                    <p><strong>VPC ID:</strong> ${tg.vpc_id}</p>
                    <p><strong>负载均衡器:</strong> ${tg.load_balancer_name || 'N/A'}</p>
                `;

                // 显示 Targets
                if (tg.targets && tg.targets.length > 0) {
                    detailHtml += `
                        <h3>Target 详细信息</h3>
                        <table id="targets-table" border="1" style="width:100%; border-collapse:collapse; margin-top:10px;">
                            <thead>
                                <tr>
                                    <th style="padding:6px 8px;background:#f0f0f0;">IP 地址</th>
                                    <th style="padding:6px 8px;background:#f0f0f0;">端口</th>
                                    <th style="padding:6px 8px;background:#f0f0f0;">可用区</th>
                                    <th style="padding:6px 8px;background:#f0f0f0;">健康状态</th>
                                    <th style="padding:6px 8px;background:#f0f0f0;">健康详情</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tg.targets.map(t => `
                                    <tr>
                                        <td style="padding:6px 8px;">${t.ip_address}</td>
                                        <td style="padding:6px 8px;">${t.port}</td>
                                        <td style="padding:6px 8px;">${t.availability_zone}</td>
                                        <td style="padding:6px 8px; color:${t.health_status === 'healthy' ? 'green' : 'red'}; font-weight:bold;">
                                            ${t.health_status}
                                        </td>
                                        <td style="padding:6px 8px;">${t.health_status_details || ''}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                } else {
                    detailHtml += `<p>该 Target Group 下暂无 Target 信息。</p>`;
                }

                $("#tg-detail-container").html(detailHtml).show();
            },
            error: function (xhr, status, error) {
                console.error("加载 Target Group 详情失败:", status, error);
                $("#tg-detail-container").html("<p>加载失败，请检查网络或 API</p>").show();
            }
        });
    }
});
