$(function() {
  $('input[name="date"]').daterangepicker({
    "singleDatePicker": true,
    "autoApply": true,
    "linkedCalendars": false,
    "showCustomRangeLabel": false,
    "locale": {
      "format": "YYYY-MM-DD"
    },
    "firstDay": 1
    }, function(start, end, label) {
      console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
    });
});
