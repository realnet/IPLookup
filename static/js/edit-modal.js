// edit-modal.js
$(document).ready(function() {
    // 获取模态框
    var modal = $('#edit-modal');
    // 获取关闭按钮
    var closeBtn = $('.close');
    // 获取取消按钮
    var cancelBtn = $('#cancel-edit');

    // 点击关闭按钮或取消按钮时关闭模态框
    closeBtn.click(function() {
        modal.css('display', 'none');
    });

    cancelBtn.click(function() {
        modal.css('display', 'none');
    });

    // 点击模态框外部时关闭模态框
    $(window).click(function(event) {
        if (event.target == modal[0]) {
            modal.css('display', 'none');
        }
    });

    // 提交编辑表单
    $('#submit-edit').click(function() {
        var recordId = $('#record-id').val();
        var newName = $('#record-name').val();
        var newType = $('#record-type').val();
        var newRoutingPolicy = $('#routing-policy').val();
        var newValue = $('#record-value').val();
        var newTTL = $('#ttl').val();

        var payload = {
            record_id: recordId,
            new_data: {
                record_name: newName,
                record_type: newType,
                routing_policy: newRoutingPolicy,
                value: newValue.split(",").map(v => v.trim()),
                ttl: parseInt(newTTL, 10)
            }
        };

        // 获取 CSRF 令牌
        var csrftoken = $('input[name=csrfmiddlewaretoken]').val();

        // 发送请求
        $.ajax({
            url: '/api/aws/route53/tasks/',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(payload),
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(data) {
                if (data.task_id) {
                    alert(`Created change task: ${data.task_id}`);
                    // 可以刷新任务列表
                    showTasks();
                    // 关闭模态框
                    modal.css('display', 'none');
                } else {
                    alert("Create task failure: " + JSON.stringify(data));
                }
            },
            error: function(err) {
                console.error(err);
                alert('An error occurred while creating the task. Please try again.');
            }
        });
    });
});