$(function() {
  $('input[name="date"]').daterangepicker({
    "singleDatePicker": true,
    "autoApply": true,
    "linkedCalendars": false,
    "showCustomRangeLabel": false,
    "autoUpdateInput": true,
    "locale": {
        "format": "YYYY-MM-D"
    },
    "firstDay": 1
    }).on("hide.daterangepicker",function (ev) {
        this.dispatchEvent(new Event('input'))
    });
});
