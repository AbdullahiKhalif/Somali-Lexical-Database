$(document).ready(function() {
    let currentPage = 1;
    const rowsPerPage = 10;
    let totalPages = 1;
    let dataCache = []; // Cache for the data

    fetchReportsData();

    function fetchReportsData(query = '') {
        $.ajax({
            url: '/reports_data',
            method: 'GET',
            data: { query: query },
            success: function(data) {
                dataCache = data; // Cache the full data
                totalPages = Math.ceil(data.length / rowsPerPage); // Calculate total pages
                displayPage(currentPage); // Show the first page
                updatePaginationInfo();
            },
            error: function(error) {
                console.error('Error fetching reports data:', error);
            }
        });
    }

    function displayPage(page) {
        let startIndex = (page - 1) * rowsPerPage;
        let endIndex = startIndex + rowsPerPage;
        let tbody = '';

        const pageData = dataCache.slice(startIndex, endIndex);

        if (pageData.length > 0) {
            pageData.forEach(function(item, index) {
                let faracWords = item.Farac.split(',').map(word => word.trim()).join(', ');

                tbody += `<tr class="bg-white hover:bg-gray-100 transition">
                    <td class="border px-4 py-2">${startIndex + index + 1}</td>
                    <td class="border px-4 py-2">${item.Asalka_erayga}</td>
                    <td class="border px-4 py-2">${faracWords}</td>
                    <td class="border px-4 py-2">${item.Qaybta_hadalka}</td>
                    <td class="border px-4 py-2">${item.total_farac}</td>
                </tr>`;
            });
        } else {
            tbody = '<tr><td colspan="5" class="text-center px-4 py-2">No results found</td></tr>';
        }
        
        $('#reportsTable tbody').html(tbody);
    }

    function updatePaginationInfo() {
        $('#pageInfo').text(`Page ${currentPage} of ${totalPages}`);
        $('#prevPage').prop('disabled', currentPage === 1);
        $('#nextPage').prop('disabled', currentPage === totalPages);
    }

    $('#prevPage').click(function() {
        if (currentPage > 1) {
            currentPage--;
            displayPage(currentPage);
            updatePaginationInfo();
        }
    });

    $('#nextPage').click(function() {
        if (currentPage < totalPages) {
            currentPage++;
            displayPage(currentPage);
            updatePaginationInfo();
        }
    });

    $('#searchInput').on('input', function() {
        const query = $(this).val().trim();
        currentPage = 1; // Reset to first page
        fetchReportsData(query);
    });

    // Export All Data, Not Limited to Pagination
    $('#exportReport').click(function() {
        exportTableToCSV('reports.csv', dataCache); // Pass all cached data
    });

    function exportTableToCSV(filename, data) {
        const csv = [];
        
        // Add headers
        const headers = ["Id", "Root_Word", "Derived_Words", "Part_of_Speech", "Total_Derivative_Words"];
        csv.push(headers.join(","));

        // Loop through all data (not just the current page)
        data.forEach(function(item, index) {
            let faracWords = item.Farac.split(',').map(word => word.trim()).join(', ');

            const row = [
                index + 1,
                `"${item.Asalka_erayga}"`,
                `"${faracWords}"`,
                `"${item.Qaybta_hadalka}"`,
                `"${item.total_farac}"`
            ];

            csv.push(row.join(","));
        });

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
