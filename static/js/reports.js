$(document).ready(function() {
    fetchReportsData();

    function fetchReportsData(query = '') {
        $.ajax({
            url: '/reports_data',
            method: 'GET',
            data: { query: query },
            success: function(data) {
                let tbody = '';
                if (data.length > 0) {
                    data.forEach(function(item, index) {
                        // Join Farac with a separator (e.g., ", ") if it's a list of words
                        let faracWords = item.Farac.split(',').map(word => word.trim()).join(', ');

                        tbody += `<tr>
                            <td>${index + 1}</td>
                            <td>${item.Asalka_erayga}</td>
                            <td>${faracWords}</td>
                            <td>${item.Qaybta_hadalka}</td>
                            <td>${item.total_farac}</td>
                        </tr>`;
                    });
                } else {
                    tbody = '<tr><td colspan="4" class="text-center">No results found</td></tr>';
                }
                $('#reportsTable tbody').html(tbody);
            },
            error: function(error) {
                console.error('Error fetching reports data:', error);
            }
        });
    }

    $('#searchInput').on('input', function() {
        const query = $(this).val().trim();
        fetchReportsData(query);
    });

    $('#exportReport').click(function() {
        exportTableToCSV('reports.csv');
    });

    function exportTableToCSV(filename) {
        const csv = [];
        const rows = document.querySelectorAll("#reportsTable tr");

        // Add headers
        const headers = ["Id", "Root_Word", "Derivative_Words", "Part_of_Speech", "Total Derivative Words"];
        csv.push(headers.join(","));

        for (let i = 1; i < rows.length; i++) {  // Start from 1 to skip headers
            const row = [], cols = rows[i].querySelectorAll("td");

            for (let j = 0; j < cols.length; j++) {
                // Handle any CSV formatting requirements, such as escaping commas
                row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
            }

            csv.push(row.join(","));
        }

        const csvFile = new Blob([csv.join("\n")], { type: "text/csv" });

        const downloadLink = document.createElement("a");
        downloadLink.download = filename;

        const url = window.URL.createObjectURL(csvFile);
        downloadLink.href = url;

        downloadLink.style.display = "none";
        document.body.appendChild(downloadLink);
        downloadLink.click();

        document.body.removeChild(downloadLink);
        window.URL.revokeObjectURL(url);
    }
});
