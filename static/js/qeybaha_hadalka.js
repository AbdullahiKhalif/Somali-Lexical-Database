$(document).ready(function() {
    fetchQeybahaHadalka();

    function fetchQeybahaHadalka() {
        $.ajax({
            url: '/readAll',
            method: 'GET',
            success: function(data) {
                let tbody = '';
                data.forEach(function(item, index) {
                    tbody += `<tr>
                        <td>${index + 1}</td>
                        <td>${item.Qaybta_hadalka}</td>
                        <td>${item.Loo_gaabsho}</td>
                        <td>
                            <button class="btn btn-primary btn-md edit-item" data-id="${item.Aqoonsiga_hadalka}"><i class="fa fa-edit"></i></button>
                            <button class="btn btn-danger btn-md delete-item" data-id="${item.Aqoonsiga_hadalka}"><i class="fa fa-trash"></i></button>
                        </td>
                    </tr>`;
                });
                $('#qeybahaTable tbody').html(tbody);
            },
            error: function(error) {
                console.error('Error fetching Qeybaha Hadalka:', error);
            }
        });
    }

    $('#addNewQeybaha').click(function() {
        $('#addQeybahaForm')[0].reset();
        $('#addQeybahaModal').modal('show');
    });

    $('#addQeybahaForm').submit(function(event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        let formDataObject = {};
        formData.forEach(field => {
            formDataObject[field.name] = field.value;
        });

        $.ajax({
            url: '/create',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formDataObject),
            success: function(data) {
                $('#addQeybahaModal').modal('hide');
                fetchQeybahaHadalka();
                Swal.fire('Success', data.message, 'success');
            },
            error: function(xhr) {
                console.error('Error saving Qeybaha Hadalka:', xhr);
                Swal.fire('Error', xhr.responseJSON.error, 'error');
            }
        });
    });

    $(document).on('click', '.edit-item', function() {
        const itemId = $(this).data('id');
        $.ajax({
            url: `/readInfo/${itemId}`,
            method: 'GET',
            success: function(data) {
                $('#editAqoonsiga_hadalka').val(data.Aqoonsiga_hadalka);
                $('#editQaybta_hadalka').val(data.Qaybta_hadalka);
                $('#editLoo_gaabsho').val(data.Loo_gaabsho);
                $('#editQeybahaModal').modal('show');
            },
            error: function(error) {
                console.error('Error fetching Qeybaha Hadalka details:', error);
            }
        });
    });

    $('#editQeybahaForm').submit(function(event) {
    event.preventDefault();
    const itemId = $('#editAqoonsiga_hadalka').val();
    const formData = {
        'Qaybta_hadalka': $('#editQaybta_hadalka').val(),
        'Loo_gaabsho': $('#editLoo_gaabsho').val()
    };

    $.ajax({
        url: `/update/${itemId}`,
        method: 'PUT',
        contentType: 'application/json',
        data: JSON.stringify(formData),
        success: function(data) {
            $('#editQeybahaModal').modal('hide');
            fetchQeybahaHadalka();  // Refresh the table to show updated data
            Swal.fire('Success', data.message, 'success');
        },
        error: function(xhr) {
            console.error('Error updating Qeybaha Hadalka:', xhr);
            Swal.fire('Error', xhr.responseJSON.error, 'error');
        }
    });
});


    $(document).on('click', '.delete-item', function() {
        const itemId = $(this).data('id');
        Swal.fire({
            title: 'Are you sure?',
            text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it!'
        }).then((result) => {
            if (result.isConfirmed) {
                $.ajax({
                    url: `/delete/${itemId}`,
                    method: 'DELETE',
                    success: function(data) {
                        fetchQeybahaHadalka();
                        Swal.fire('Deleted!', 'Qeybaha Hadalka has been deleted.', 'success');
                    },
                    error: function(error) {
                        console.error('Sorry! You cannot delete this data. Only the original user can delete it.:', error.responseJSON.error);
                        Swal.fire('Error', error.responseJSON.error, 'error');
                    }
                });
            }
        });
    });
});
