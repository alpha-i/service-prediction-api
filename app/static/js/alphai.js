$(document).ready(function () {
    moment.tz.setDefault('UTC');
})

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
        var last_status_index, last_status, $row;

        last_status_index = task.statuses.length - 1;
        last_status = task.statuses[last_status_index].state;

        var status_icon = '';

        switch (last_status) {
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

        var created_at = moment(task.created_at)
        $row.append('<td>' + created_at.format("YYYY-MM-DD HH:mm:ss") + '</td>');
        $row.append('<td>' + status + '</td>');
        $row.append('<td><a href="/customer/prediction/' + task.task_code + '"><i class="fa fa-list"></i></a></td>');

        var $oldRow = $('#' + task.task_code);
        $($oldRow).remove();
        $('#datasource-task-list > tbody').append($row);
    }
};

var PredictionStatusRefresh = {

    refreshStatuses: function () {

        var $prediction_table = $('table.prediction-log');
        var $is_completed = ($('table.prediction-log').data("completed").toLowerCase() == 'true');
        var $task_code = $prediction_table.attr("id")

        url = '/prediction/' + $task_code;
        if (!$is_completed) {
            $.ajax({
                url: url,
                success: PredictionStatusRefresh.OnResultLoad
            })
        }

    },
    OnResultLoad: function (prediction) {

        var task_code = prediction.task_code;

        var $prediction_table = $('table#' + task_code);
        $prediction_table.attr("data-completed", prediction.is_completed)
        $tr = $prediction_table.find('tbody tr');
        $tr.remove();
        $(prediction.statuses).each(function (i, status) {
            $row = PredictionStatusRefresh.buildRow(status)
            $prediction_table.find('tbody').append($row)
        });

        PredictionStatusRefresh.manageElapsedTime(prediction)
    },
    buildRow: function (status) {
        $row = $('<tr>');

        var created_at = moment(status.created_at);
        var cell = $('<td>').html(created_at.format("YYYY-MM-DD HH:mm:ss"));
        $row.append(cell);

        var cell = $('<td>').html(status.state);
        $row.append(cell);

        var message = status.message || "None";
        var cell = $('<td>').html(message);
        $row.append(cell);

        return $row
    },
    manageElapsedTime: function (prediction) {

        if (prediction.is_completed) {
            $('#status-spinner').hide();
            location.reload();
        } else {
            $duration = moment.duration(moment() - moment(prediction.created_at))
            $duration_string = $duration.format('hh:mm:ss');
            $elapsed_time = $("#elapsed-prediction-time").html($duration_string);
        }
    }
};

var ChartDecorator = {
    colors: ['rgba(11,59,95,1)', 'rgba(115,57,117,1)', 'rgba(246,247,72,1)', 'rgba(59,204,123,1)', 'rgba(234,99,180,1)', 'rgba(145,74,149,1)', 'rgba(79,150,194,1)', 'rgba(186,21,8,1)', 'rgba(139,232,10,1)', 'rgba(183,17,53,1)', 'rgba(103,232,248,1)', 'rgba(233,3,100,1)', 'rgba(77,249,111,1)', 'rgba(180,16,177,1)', 'rgba(188,90,127,1)', 'rgba(23,237,253,1)', 'rgba(111,9,178,1)', 'rgba(181,134,5,1)', 'rgba(157,11,37,1)', 'rgba(155,239,131,1)', 'rgba(239,251,93,1)', 'rgba(149,164,213,1)', 'rgba(111,234,128,1)', 'rgba(156,116,220,1)', 'rgba(34,47,65,1)', 'rgba(167,225,88,1)', 'rgba(209,208,214,1)', 'rgba(244,140,218,1)', 'rgba(234,156,51,1)', 'rgba(10,194,97,1)', 'rgba(169,66,33,1)', 'rgba(249,139,42,1)', 'rgba(209,152,26,1)', 'rgba(190,67,162,1)', 'rgba(52,108,23,1)', 'rgba(103,164,223,1)', 'rgba(165,151,228,1)', 'rgba(203,182,151,1)', 'rgba(96,31,139,1)', 'rgba(194,244,121,1)', 'rgba(199,205,143,1)', 'rgba(222,166,240,1)', 'rgba(44,130,61,1)', 'rgba(165,133,249,1)', 'rgba(148,142,79,1)', 'rgba(126,203,115,1)', 'rgba(13,25,43,1)', 'rgba(36,69,203,1)', 'rgba(23,54,189,1)', 'rgba(49,121,212,1)'],
    transparent_colors: ['rgba(11,59,95,0.25)', 'rgba(115,57,117,0.25)', 'rgba(246,247,72,0.25)', 'rgba(59,204,123,0.25)', 'rgba(234,99,180,0.25)', 'rgba(145,74,149,0.25)', 'rgba(79,150,194,0.25)', 'rgba(186,21,8,0.25)', 'rgba(139,232,10,0.25)', 'rgba(183,17,53,0.25)', 'rgba(103,232,248,0.25)', 'rgba(233,3,100,0.25)', 'rgba(77,249,111,0.25)', 'rgba(180,16,177,0.25)', 'rgba(188,90,127,0.25)', 'rgba(23,237,253,0.25)', 'rgba(111,9,178,0.25)', 'rgba(181,134,5,0.25)', 'rgba(157,11,37,0.25)', 'rgba(155,239,131,0.25)', 'rgba(239,251,93,0.25)', 'rgba(149,164,213,0.25)', 'rgba(111,234,128,0.25)', 'rgba(156,116,220,0.25)', 'rgba(34,47,65,0.25)', 'rgba(167,225,88,0.25)', 'rgba(209,208,214,0.25)', 'rgba(244,140,218,0.25)', 'rgba(234,156,51,0.25)', 'rgba(10,194,97,0.25)', 'rgba(169,66,33,0.25)', 'rgba(249,139,42,0.25)', 'rgba(209,152,26,0.25)', 'rgba(190,67,162,0.25)', 'rgba(52,108,23,0.25)', 'rgba(103,164,223,0.25)', 'rgba(165,151,228,0.25)', 'rgba(203,182,151,0.25)', 'rgba(96,31,139,0.25)', 'rgba(194,244,121,0.25)', 'rgba(199,205,143,0.25)', 'rgba(222,166,240,0.25)', 'rgba(44,130,61,0.25)', 'rgba(165,133,249,0.25)', 'rgba(148,142,79,0.25)', 'rgba(126,203,115,0.25)', 'rgba(13,25,43,0.25)', 'rgba(36,69,203,0.25)', 'rgba(23,54,189,0.25)', 'rgba(49,121,212,0.25)'],
    getChartColors: function (data_length) {

        var data = [];
        for (var i = 0; i < data_length; i++) {
            data.push(ChartDecorator.getSingleColorWrap(i))
        }
        return data
    },
    getSingleColorWrap: function (i) {
        var color_length = ChartDecorator.colors.length;
        var index = (i > color_length) ? i % color_length : i;

        return ChartDecorator.colors[index]
    },
    getSingleAlphaColorWrap: function (i) {
        var color_length = ChartDecorator.transparent_colors.length;
        var index = (i > color_length) ? i % color_length : i;

        return ChartDecorator.transparent_colors[index]
    },
    getAlphaChartColors: function (data_length) {
        var data = [];
        for (var i = 0; i < data_length; i++) {
            data.push(ChartDecorator.getSingleAlphaColorWrap(i))
        }
        return data
    }
};
