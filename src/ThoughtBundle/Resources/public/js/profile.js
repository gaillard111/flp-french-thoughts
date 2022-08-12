$(document).ready(function () {
    let $modal = $('#request-personal-data-modal')

    $('#request-personal-data-btn').click(function (e) {
        e.preventDefault()

        let url = $(this).data('url')

        $.ajax({
            method: "POST",
            url: url,
        }).success(function (response) {
            if (response.success) {
                showModal(true)
            } else {
                showModal(false)
            }
        }).error(function (response) {
            console.log(response.message);
        });
    })

    function showModal(success) {
        $modal.find('.success-message').toggleClass('d-none', !success)
        $modal.find('.error-message').toggleClass('d-none', success)
        $modal.modal('show')
    }
})