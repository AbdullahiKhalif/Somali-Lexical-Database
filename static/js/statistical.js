$(document).ready(function () {
    // Fetch the statistical data and initialize charts
    fetchStatisticalData();

    // Function to fetch the statistical data and draw the chart
    function fetchStatisticalData() {
        $.get('/statistical_data', function (response) {
            // Populate the stats at the top
            $('#total_asalka_ereyada').text(response.total_asalka_ereyada || 0);
            $('#total_faraca_erayada').text(response.total_faraca_erayada || 0);
            $('#total_asalka_with_farac').text(response.total_asalka_with_farac || 0);
            $('#total_farac_with_asal').text(response.total_farac_with_asal || 0);
            $('#max_derivatives').text(response.max_derivatives || 0);
            $('#min_derivatives').text(response.min_derivatives || 0);

            // Prepare data for the Qaybta_hadalka distribution chart
            const labels = [];
            const countData = [];

            response.qaybta_hadalka_distribution.forEach(function (item) {
                labels.push(item.Qaybta_hadalka); // Part of Speech (Qaybta_hadalka)
                countData.push(item.asal_count); // Number of Asalka Ereyga
            });

            // Call the function to draw the improved histogram chart
            drawQaybtaHadalkaHistogram(labels, countData);
        }).fail(function (xhr) {
            console.error('Error fetching statistical data:', xhr);
        });
    }

    // Function to draw the improved Qaybta_hadalka histogram chart
    function drawQaybtaHadalkaHistogram(labels, countData) {
        const ctx = document.getElementById('qaybtaAsalkaChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels, // X-axis: Part of Speech (Qaybta_hadalka)
                datasets: [{
                    label: 'Number of Root Words (Asalka Ereyga)',
                    data: countData, // Y-axis: Count of Root Words (Asalka Ereyga)
                    backgroundColor: 'rgba(54, 162, 235, 0.7)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top' // Position the legend at the top
                    },
                    datalabels: {
                        display: true, // Enable data labels on bars
                        align: 'top',
                        color: '#333',
                        font: {
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Part of Speech (Qaybta_hadalka)',
                            color: '#333',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Root Words (Asalka Ereyga)',
                            color: '#333',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                }
            }
        });
    }
});
