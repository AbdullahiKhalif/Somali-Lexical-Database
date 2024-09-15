$(document).ready(function() {
    // Fetch dashboard data
    $.get('/dashboard_data', function(data) {
        // Update total users, Asalka Ereydada, and Faraca Erayada counts
        $('#total_users').text(data.total_users);
        $('#total_asalka_ereyada').text(data.total_asalka_ereyada);
        $('#total_faraca_erayada').text(data.total_faraca_erayada);

        // Gender Distribution Chart
        const genderChartCtx = document.getElementById('genderChart').getContext('2d');
        new Chart(genderChartCtx, {
            type: 'pie',
            data: {
                labels: data.gender_distribution.map(item => item.gender),
                datasets: [{
                    data: data.gender_distribution.map(item => item.count),
                    backgroundColor: ['#007bff', '#21a741', '#dc3545'],
                    borderColor: '#ffffff',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    datalabels: {
                        color: '#ffffff',
                        display: true,
                        font: {
                            weight: 'bold',
                            size: 14
                        },
                        formatter: (value, context) => {
                            let sum = 0;
                            let dataArr = context.chart.data.datasets[0].data;
                            dataArr.forEach(data => {
                                sum += data;
                            });
                            let percentage = (value * 100 / sum).toFixed(2) + "%";
                            return `${value} (${percentage})`;
                        }
                    }
                }
            }
        });

        // Asalka vs Faraca Chart
        const asalkaFaracaChartCtx = document.getElementById('asalkaFaracaChart').getContext('2d');
        new Chart(asalkaFaracaChartCtx, {
            type: 'pie',
            data: {
                labels: ['Total Asalka Ereydada', 'Total Faraca Erayada'],
                datasets: [{
                    data: [data.total_asalka_ereyada, data.total_faraca_erayada],
                    backgroundColor: ['#17a2b8', '#ffc107'],
                    borderColor: '#ffffff',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    datalabels: {
                        color: '#ffffff',
                        display: true,
                        font: {
                            weight: 'bold',
                            size: 14
                        },
                        formatter: (value, context) => {
                            let sum = data.total_asalka_ereyada + data.total_faraca_erayada;
                            let percentage = (value * 100 / sum).toFixed(2) + "%";
                            return `${value} (${percentage})`;
                        }
                    }
                }
            }
        });

        // Age Distribution Histogram
        const ageDistributionCtx = document.getElementById('ageDistributionChart').getContext('2d');
        new Chart(ageDistributionCtx, {
            type: 'bar',
            data: {
                labels: data.age_distribution.map(item => item.age), // Assuming you have discrete age values
                datasets: [{
                    label: 'Age Distribution',
                    data: data.age_distribution.map(item => item.count),
                    backgroundColor: '#007bff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    barPercentage: 1.0,
                    categoryPercentage: 1.0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    datalabels: {
                        color: '#ffffff',
                        display: true,
                        font: {
                            weight: 'bold',
                            size: 12
                        },
                        formatter: (value) => value
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 5 // Assuming age is grouped in bins of 5 years
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    });
});
