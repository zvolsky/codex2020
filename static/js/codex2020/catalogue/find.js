$(document).ready(function() {

    $('input:submit').hide();

    $('#no_table_appendkey').on('change', function() {
        $('#nabidka_nalezenych').html('hledá se ...');
        ajax('http://localhost:8000/codex2020/katalogizace/hledej_appendkey',
                ['appendkey'], 'nabidka_nalezenych');
    });

});
