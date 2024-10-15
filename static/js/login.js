// Ensure jQuery is loaded before executing the script
$(document).ready(function() {
    // Attach a submit event listener to the form with ID 'login-form'
    $("#login-form").on("submit", function(event) {
        // Prevent the default form submission behavior
        event.preventDefault();

        // Serialize the form data
        var formData = $(this).serialize();

        // Make an AJAX POST request to the server
        $.ajax({
            type: "POST",
            url: "/login",  // Change this to your login endpoint URL if different
            data: formData,
            success: function(response) {
                // Check if there's an error in the response
                if (response.error) {
                    // Display the error message using SweetAlert
                    Swal.fire({
                        icon: "error",
                        title: "Login Failed",
                        text: response.error,
                        showConfirmButton: true
                    });
                } else {
                    // If no error, redirect to the dashboard or another page
                    window.location.href = "/dashboard";  // Change this to your dashboard URL if different
                }
            },
            error: function(xhr, status, error) {
                // Handle any errors that occur during the request
                Swal.fire({
                    icon: "error",
                    title: "An Error Occurred",
                    text: "Unable to process your request. Please try again later.",
                    showConfirmButton: true
                });
            }
        });
    });
});
