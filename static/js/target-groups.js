$(document).ready(function () {
    let allTargetGroups = [];
    let currentPage = 1;
    let pageSize = 10;

    // 点击菜单项加载 Target Groups
    $("#menu-target-groups").click(function (e) {
        e.preventDefault();
        loadTargetGroups();
    });

    function loadTargetGroups() {
        const welcomeSection = $("#welcome-section");
        const targetGroupsContainer = $("#target-groups-container");

        console.log("targetGroupsContainer 是否存在:", targetGroupsContainer.length > 0);

        if (welcomeSection.length) welcomeSection.hide();
        if (targetGroupsContainer.length) {
            targetGroupsContainer.show();
        } else {
            console.error("无法找到 #target-groups-container");
            return;
        }

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

    function renderTable() {
        const tableBody = $("#tg-table-body");
        tableBody.empty();

        if (allTargetGroups.length === 0) {
            tableBody.append("<tr><td colspan='6'>暂无数据</td></tr>");
            return;
        }

        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;
        const paginatedData = allTargetGroups.slice(start, end);

        paginatedData.forEach(tg => {
            const row = `
                <tr data-id="${tg.id}">
                    <td class="tg-name" style="cursor:pointer;color:#09853c;text-decoration:underline;">
                        ${tg.name}
                    </td>
                    <td>${tg.protocol}</td>
                    <td>${tg.port}</td>
                    <td>${tg.target_type}</td>
                    <td>${tg.vpc_id}</td>
                    <td>${tg.load_balancer_name || 'N/A'}</td>
                </tr>
            `;
            tableBody.append(row);
        });

        $(".tg-name").off("click").on("click", function () {
            const tgId = $(this).closest("tr").data("id");
            loadTargetGroupDetail(tgId);
        });

        updatePagination();
    }

    function updatePagination() {
        const paginationContainer = $("#pagination-container");
        paginationContainer.empty();

        if (allTargetGroups.length === 0) {
            paginationContainer.append("<p>暂无数据</p>");
            return;
        }

        const totalPages = Math.ceil(allTargetGroups.length / pageSize);

        let paginationHtml = `
            <button id="prev-page" ${currentPage === 1 ? "disabled" : ""}>上一页</button>
            <span> 第 ${currentPage} 页 / 共 ${totalPages} 页 </span>
            <button id="next-page" ${currentPage === totalPages ? "disabled" : ""}>下一页</button>
            <select id="page-size-select">
                <option value="10" ${pageSize === 10 ? "selected" : ""}>10</option>
                <option value="20" ${pageSize === 20 ? "selected" : ""}>20</option>
                <option value="50" ${pageSize === 50 ? "selected" : ""}>50</option>
                <option value="100" ${pageSize === 100 ? "selected" : ""}>100</option>
            </select>
        `;

        paginationContainer.append(paginationHtml);

        $("#prev-page").off("click").on("click", function () {
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });

        $("#next-page").off("click").on("click", function () {
            if (currentPage < totalPages) {
                currentPage++;
                renderTable();
            }
        });

        $("#page-size-select").off("change").on("change", function () {
            pageSize = parseInt($(this).val());
            currentPage = 1;
            renderTable();
        });
    }

    function loadTargetGroupDetail(tgId) {
        $.ajax({
            url: `/api/aws/target-groups/${tgId}/`,
            method: "GET",
            dataType: "json",
            success: function (tg) {
                console.log("loadTargetGroupDetail => ", tg);

                if (!tg || typeof tg!== "object") {
                    console.error("API 详情数据格式错误:", tg);
                    $("#tg-detail-container").html("<p>无法加载详情，请检查 API 响应</p>").show();
                    return;
                }

                const detailHtml = `
                    <h3>Target Group 详情</h3>
                    <p><strong>名称:</strong> ${tg.name}</p>
                    <p><strong>协议:</strong> ${tg.protocol}</p>
                    <p><strong>端口:</strong> ${tg.port}</p>
                    <p><strong>目标类型:</strong> ${tg.target_type}</p>
                    <p><strong>VPC ID:</strong> ${tg.vpc_id}</p>
                    <p><strong>负载均衡器:</strong> ${tg.load_balancer_name || 'N/A'}</p>
                `;

                $("#tg-detail-container").html(detailHtml).show();

                // 显示 Target 详细信息表格
                if (tg.targets && tg.targets.length > 0) {
                    const targetTableHtml = `
                        <h3>Target 详细信息</h3>
                        <table id="targets-table">
                            <thead>
                                <tr>
                                    <th>ip_address</th>
                                    <th>port</th>
                                    <th>availability_zone</th>
                                    <th>health_status</th>
                                    <th>health_status_details</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${tg.targets.map(target => `
                                    <tr>
                                        <td>${target.ip_address}</td>
                                        <td>${target.port}</td>
                                        <td>${target.availability_zone}</td>
                                        <td>${target.health_status}</td>
                                        <td>${target.health_status_details}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    $("#tg-detail-container").append(targetTableHtml);
                } else {
                    $("#tg-detail-container").append("<p>该 Target Group 下暂无 Target 信息。</p>");
                }
            },
            error: function (xhr, status, error) {
                console.error("加载 Target Group 详情失败:", status, error);
                $("#tg-detail-container").html("<p>加载失败，请检查网络或 API</p>").show();
            }
        });
    }
});