$(document).ready(function() {
    fetchAsalkaEreyada();

    function fetchAsalkaEreyada() {
        $.ajax({
            url: '/readAllAsalka',
            method: 'GET',
            success: function(response) {
                let tbody = '';
                response.data.forEach(function(item, index) {
                    tbody += `<tr>
                        <td>${index + 1}</td>
                        <td>${item.Erayga_Asalka}</td>
                        <td>
                            <button class="btn btn-primary btn-md edit-item" data-id="${item.Aqonsiga_Erayga}"><i class="fa fa-edit"></i></button>
                            <button class="btn btn-danger btn-md delete-item" data-id="${item.Aqonsiga_Erayga}"><i class="fa fa-trash"></i></button>
                        </td>
                    </tr>`;
                });
                $('#asalkaTable tbody').html(tbody);
                $('#total_records').text(response.total_records); // Display the total records count
            },
            error: function(error) {
                console.error('Error fetching Asalka Ereyada:', error);
            }
        });
    }

    $('#addNewAsalka').click(function() {
        $('#addAsalkaForm')[0].reset();
        $('#addAsalkaModal').modal('show');
    });

    $('#addAsalkaForm').submit(function(event) {
        event.preventDefault();
        const formData = $(this).serializeArray();
        let formDataObject = {};
        formData.forEach(field => {
            formDataObject[field.name] = field.value;
        });

        $.ajax({
            url: '/createAsalka',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formDataObject),
            success: function(data) {
                $('#addAsalkaModal').modal('hide');
                fetchAsalkaEreyada();
                Swal.fire('Success', data.message, 'success');
            },
            error: function(xhr) {
                console.error('Error saving Asalka Ereyada:', xhr);
                const response = xhr.responseJSON;
                Swal.fire('Error', response.error, 'error');
            }
        });
    });

    $(document).on('click', '.edit-item', function() {
        const itemId = $(this).data('id');
        $.ajax({
            url: `/readInfoAsalka/${itemId}`,
            method: 'GET',
            success: function(data) {
                $('#editAqonsiga_Erayga').val(data.Aqonsiga_Erayga);
                $('#editErayga_Asalka').val(data.Erayga_Asalka);
                $('#editAsalkaModal').modal('show');
            },
            error: function(error) {
                console.error('Error fetching Asalka Ereyada details:', error);
            }
        });
    });

    $('#editAsalkaForm').submit(function(event) {
        event.preventDefault();
        const itemId = $('#editAqonsiga_Erayga').val();
        const formData = $(this).serializeArray();
        let formDataObject = {};
        formData.forEach(field => {
            formDataObject[field.name] = field.value;
        });

        $.ajax({
            url: `/updateAsalka/${itemId}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(formDataObject),
            success: function(data) {
                $('#editAsalkaModal').modal('hide');
                fetchAsalkaEreyada();
                Swal.fire('Success', data.message, 'success');
            },
            error: function(xhr) {
                console.error('Error updating Asalka Ereyada:', xhr);
                const response = xhr.responseJSON;
                Swal.fire('Error', response.error, 'error');
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
                    url: `/deleteAsalka/${itemId}`,
                    method: 'DELETE',
                    success: function(data) {
                        fetchAsalkaEreyada();
                        Swal.fire('Deleted!', 'Asalka Ereyada has been deleted.', 'success');
                    },
                    error: function(error) {
                        console.error('Error deleting Asalka Ereyada:', error);
                        Swal.fire('Error', 'Failed to delete Asalka Ereyada', 'error');
                    }
                });
            }
        });
    });

    // Show the Upload Modal when the upload button is clicked
    $('#uploadAsalka').click(function() {
        $('#uploadAsalkaForm')[0].reset();
        $('#uploadAsalkaModal').modal('show');
    });

    // Handle form submission for uploading Excel file
    $('#uploadAsalkaForm').submit(function(event) {
        event.preventDefault();
        const formData = new FormData(this);

        $.ajax({
            url: '/uploadAsalka',
            method: 'POST',
            processData: false,
            contentType: false,
            data: formData,
            success: function(data) {
                $('#uploadAsalkaModal').modal('hide');
                fetchAsalkaEreyada(); // Refresh the table after upload
                Swal.fire('Success', data.message, 'success');
            },
           error: function(xhr) {
    console.error('Error uploading Asalka Ereyada:', xhr);
    const response = xhr.responseJSON || {};
    Swal.fire('Error', response.error || 'Failed to upload Asalka Ereyada. Please check your connection and try again.', 'error');
}

        });
    });
});
