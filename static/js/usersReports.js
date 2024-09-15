$(document).ready(function() {
    fetchUserReports();

    function fetchUserReports() {
        $.ajax({
            url: '/user_reports',
            method: 'GET',
            success: function(data) {
                let tbody = '';
                if (data.length > 0) {
                    data.forEach(function(item, index) {
                        tbody += `<tr>
                            <td>${index + 1}</td>
                            <td>${item.name}</td>
                            <td>${item.total_asalka_recorded}</td>
                            <td>${item.total_rafaca_erayada}</td>
                            <td>${item.total_count}</td>
                        </tr>`;
                    });
                } else {
                    tbody = '<tr><td colspan="5" class="text-center">No data available</td></tr>';
                }
                $('#userReportTable tbody').html(tbody);
            },
            error: function(error) {
                console.error('Error fetching user reports:', error);
                alert('An error occurred while fetching the data. Please try again later.');
            }
        });
    }
});
