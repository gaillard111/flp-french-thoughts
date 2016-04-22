$(function(){
    $('.jumbotron .like-quote').on('click', function(e){
        e.preventDefault();
        var button = $(this),
            badge = button.find('span.badge'),
            badgeText = button.find('span.badge-text'),
            quoteId = button.data('quote');

        $.ajax({
            url : Routing.generate('thought-like', {'thoughtId': quoteId}),
            dataType: "json",
            success: function(data) {
                badge.text(data.count);

                if (data.count > 0) {
                    badge.css('display', 'inline-block');
                } else {
                    badge.hide();
                }

                if (data.result == 'add') {
                    badgeText.text('Liked');
                } else {
                    badgeText.text('Like');
                }

                console.log(data);
            }
        });
    });
});
