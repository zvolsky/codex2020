$(document).ready(function() {

    $('#publikace_appendkey').on('change', function() {
        ajax('http://localhost:8000/codex2020/katalogizace/hledej_appendkey',
                ['appendkey'], 'nabidka_nalezenych');
    });
});
