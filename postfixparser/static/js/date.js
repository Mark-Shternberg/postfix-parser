$(function() {
  $('input[name="date"]').daterangepicker({
    "singleDatePicker": true,
    "autoApply": true,
    "linkedCalendars": false,
    "showCustomRangeLabel": false,
    "startDate": "04/03/2023",
    "endDate": "04/09/2023"
    }, function(start, end, label) {
      console.log('New date range selected: ' + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD') + ' (predefined range: ' + label + ')');
    });
});
