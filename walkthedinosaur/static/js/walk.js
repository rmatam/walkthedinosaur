jQuery(function($) {
    console.log('hi there');
    console.log($('#tablename').val());
    tables = tables.replace(/&quot;/g, '"')
    tables = $.parseJSON(tables)

    var get_columns = function(tablename) {
        $("#field option").remove();
        $.each(tables[tablename], function(i, column) {
            $("#field").append("<option value='"+column+"'>"+column+"</option>");
        });
    }

    get_columns($('#tablename').val());

    $('#tablename').change( function() {
        var tablename = $('#tablename').val()
        console.log(tablename);
        get_columns(tablename)
    });

});
