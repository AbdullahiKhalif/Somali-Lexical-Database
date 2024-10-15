$(document).ready(function () {
    // Fetch dashboard data
    $.get('/dashboard_data', function (data) {
        // Get the user's role
        const userRole = data.user_role;

        // Show/hide sections based on the user role
        if (userRole === 'Admin') {
            // Show all cards and charts for Admin
            $('#total_users_card').show();
            $('#total_admins_card').show();
            $('#total_moderators_card').show();
            $('#total_regular_users_card').show();
            $('#max_derivatives_card').show();
            $('#min_derivatives_card').show();
            $('#charts_row').show(); // Show charts for Admin

            // Update admin-specific data
            $('#total_users').text(data.total_users);
            $('#total_admins').text(data.total_admins);
            $('#total_moderators').text(data.total_moderators);
            $('#total_regular_users').text(data.total_regular_users);
            $('#total_approved').text(data.total_approved);
            $('#total_pendings').text(data.total_pendings);
            $('#total_declined').text(data.total_declined);
            $('#total_actives').text(data.total_actives);
            $('#total_blocks').text(data.total_blocks);
            $('#max_derivatives').text(data.max_derivatives);
            $('#min_derivatives').text(data.min_derivatives);
            $('#total_asalka_ereyada').text(data.total_asalka_ereyada);
            $('#total_faraca_erayada').text(data.total_faraca_erayada);

            
            $('#total_asalka_with_farac').text(data.total_asalka_with_farac);
            $('#total_farac_with_asal').text(data.total_farac_with_asal);


            // Render charts for Admin
            renderCharts(data);

        } else if (userRole === 'User' || userRole === 'Moderator') {
            // Show only root words and descendant words for User/Moderator
            $('#total_asalka_ereyada_card').show();
            $('#total_faraca_erayada_card').show();

            // Update user-specific data
            $('#total_asalka_ereyada_user').text(data.total_asalka_ereyada);
            $('#total_faraca_erayada_user').text(data.total_faraca_erayada);


            // Hide admin-specific elements
            $('#total_users_card').hide();
            $('#total_admins_card').hide();
            $('#total_moderators_card').hide();
            $('#total_regular_users_card').hide();
            $('#max_derivatives_card').hide();
            $('#min_derivatives_card').hide();
            $('#charts_row').hide(); // Hide charts for User/Moderator
        }
    });
});

// Function to render charts (only for Admin)
function renderCharts(data) {
    // User Role Distribution Chart
    const userRoleChartCtx = document.getElementById('userRoleChart').getContext('2d');
    new Chart(userRoleChartCtx, {
        type: 'pie',
        data: {
            labels: data.user_role_distribution.map(item => item.userRole),
            datasets: [{
                data: data.user_role_distribution.map(item => item.count),
                backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'], // Customize colors
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
                        let sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        let percentage = (value * 100 / sum).toFixed(2) + "%";
                        return `${value} (${percentage})`;
                    }
                }
            }
        }
    });

    // User State Distribution Chart
    const userStateChartCtx = document.getElementById('userStateChart').getContext('2d');
    new Chart(userStateChartCtx, {
        type: 'pie',
        data: {
            labels: data.user_state_distribution.map(item => item.userState),
            datasets: [{
                data: data.user_state_distribution.map(item => item.count),
                backgroundColor: ['#28a745', '#000', '#1F9BCF', '#ffc107'], // Customize colors
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
                        let sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        let percentage = (value * 100 / sum).toFixed(2) + "%";
                        return `${value} (${percentage})`;
                    }
                }
            }
        }
    });

    // User Status Distribution Chart
    const userStatusChartCtx = document.getElementById('userStatusChart').getContext('2d');
    new Chart(userStatusChartCtx, {
        type: 'pie',
        data: {
            labels: data.user_status_distribution.map(item => item.status),
            datasets: [{
                data: data.user_status_distribution.map(item => item.count),
                backgroundColor: ['#07B32F', '#dc3545',], // Customize colors
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
                        let sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        let percentage = (value * 100 / sum).toFixed(2) + "%";
                        return `${value} (${percentage})`;
                    }
                }
            }
        }
    });

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

    // Asalka vs Faraca Chart (Root vs Descendant Words)
    const asalkaFaracaChartCtx = document.getElementById('asalkaFaracaChart').getContext('2d');
    new Chart(asalkaFaracaChartCtx, {
        type: 'pie',
        data: {
            labels: ['Total Root Words', 'Total Derivatives Words'],
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


}
