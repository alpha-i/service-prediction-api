var DatasourceRefresh = {
    refreshTaskCode: function () {

        $('#datasource-task-list tr.task-row')
            .filter(DatasourceRefresh.isTaskInProgress)
            .each(DatasourceRefresh.reloadTask);
    },
    isTaskInProgress: function (i, task) {
        var task_status = $(task).data("completed");
        return (task_status.toLowerCase() == "false");
    },
    reloadTask: function (i, el) {
        var task_code = $(el).attr('id');
        var url = '/prediction/' + task_code;
        $.ajax({
            url: url,
            success: DatasourceRefresh.refreshRow
        });
    },
    refreshRow: function (task) {
        var last_status_index, last_status, view_task, $row;

        last_status_index = task.statuses.length - 1;
        last_status = task.statuses[last_status_index].state;

        var status_icon = '';

        switch(last_status) {
            case 'SUCCESSFUL' : {
                status_icon = 'fa-check-circle text-green'
            }
            break;
            case 'FAILED': {
                status_icon = 'fa-warning text-yellow'
            }
            break;
            default: {
                status_icon = 'fa-refresh fa-spin'
            }
        }

        status = '<i class="fa ' + status_icon + '" alt="' + last_status + '"></i>';

        $row = $('<tr>');
        $row.attr("id", task.task_code).addClass("task-row");
        $row.attr("data-completed", task.is_completed ? "True" : "False");
        $row.append('<td scope="row">' + task.name + '</td>');
        $row.append('<td scope="row">' + task.task_code + '</td>')
        $row.append('<td>' + task.created_at + '</td>');
        $row.append('<td>' + status + '</td>');
        $row.append('<td><a href="/customer/prediction/' + task.task_code + '"><i class="fa fa-list"></i></a></td>');

        var $oldRow = $('#' + task.task_code);
        $($oldRow).remove();
        $('#datasource-task-list > tbody').append($row);
    }
}
