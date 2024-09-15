$(document).ready(function() {
    fetchReportsRootWords();

    function fetchReportsRootWords() {
        $.ajax({
            url: '/readAllAsalkaOrderedByUsername',
            method: 'GET',
            success: function(data) {
                let tbody = '';
                if (data.length > 0) {
                    data.forEach(function(item, index) {
                        tbody += `<tr>
                            <td>${index + 1}</td>
                            <td>${item.Erayga_Asalka}</td>
                            <td>${item.name}</td>
                        </tr>`;
                    });
                } else {
                    tbody = '<tr><td colspan="3" class="text-center">No results found</td></tr>';
                }
                $('#reportsTable tbody').html(tbody);
            },
            error: function(error) {
                console.error('Error fetching root words data:', error);
            }
        });
    }
});
