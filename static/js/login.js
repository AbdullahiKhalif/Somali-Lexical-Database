$("#form").on("submit", function(event) {
    event.preventDefault();

    $.ajax({
        type: 'POST',
        url: '/login',
        data: $('#form').serialize(),
        success: function(response) {
            if(response.error) {
                const Toast = Swal.mixin({
                toast: true,
                position: "top-right",
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.onmouseenter = Swal.stopTimer;
                    toast.onmouseleave = Swal.resumeTimer;
                }
            });
            Toast.fire({
                icon: "error",
                title: response.error
            });
            return;
            }
            // redirect home page
            window.location.href = "{{ url_for('dashboard') }}";
        },

})
});