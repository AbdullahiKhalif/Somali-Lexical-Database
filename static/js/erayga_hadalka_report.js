$(document).ready(function() {
    // Fetch the report data on page load
    fetchReportData();

    // Function to fetch the report data
    function fetchReportData() {
        $.ajax({
            url: '/report',  // Assuming /report is the endpoint to fetch the report data
            method: 'GET',
            success: function(data) {
                populateTable(data);
            },
            error: function(error) {
                console.error('Error fetching report data:', error);
                alert('Failed to fetch the report data.');
            }
        });
    }

    // Function to populate the table with report data
    function populateTable(data) {
        let tableBody = '';
        data.forEach(function(item, index) {
            tableBody += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${item.Asalka_erayga_name}</td>
                    <td>${item.Erayga}</td>
                    <td>${item.Qeybta_hadalka_name}</td>
                </tr>`;
        });
        $('#reportsTable tbody').html(tableBody);
    }

    // Function to export table data to CSV
    $('#exportReport').click(function() {
        exportTableToCSV('reports.csv');
    });

    function exportTableToCSV(filename) {
        const csv = [];
        const headers = [];

        // Get headers
        $('#reportsTable thead th').each(function() {
            headers.push($(this).text().trim());
        });
        csv.push(headers.join(","));

        // Get rows data
        $('#reportsTable tbody tr').each(function() {
            const row = [];
            $(this).find('td').each(function() {
                row.push($(this).text().trim());
            });
            csv.push(row.join(","));
        });

        // Create a CSV file and trigger download
        const csvFile = new Blob([csv.join("\n")], { type: 'text/csv' });
        const downloadLink = document.createElement('a');
        downloadLink.download = filename;
        const url = window.URL.createObjectURL(csvFile);
        downloadLink.href = url;
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        window.URL.revokeObjectURL(url);
    }
});
