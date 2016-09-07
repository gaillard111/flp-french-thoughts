var noticer = {
    init: function(text, type) {
        var $wrap = $('div.noticer-wrap');

        if (!$wrap.length) {
            $wrap = $('<div/>').addClass('noticer-wrap');

            $('body').append($wrap);
        }

        var $item = $('<div/>').addClass('noticer-item').addClass(type).prependTo($wrap);

        $('<span/>').addClass('noticer-close')
            .html('<span aria-hidden="true">&times;</span>')
            .appendTo($item)
        ;

        $('<div/>').addClass('noticer-body').html(text).appendTo($item);

        return $item;
    },
    close: function(notice){
        notice.animate({marginLeft: "1000px"}, {
            duration: 600,
            complete: function(){
                $(this).remove();
            }
        });
    },
    success: function(text) {
        var $item = this.init(text, 'noticer-success');

        setTimeout(function(){
            noticer.close($item);
        }, 5000);
    },
    alert: function(text) {
        var $item = this.init(text, 'noticer-danger');

        setTimeout(function(){
            noticer.close($item);
        }, 5000)
    }
};

$('body').on('click', '.noticer-close', function(){
    noticer.close($(this).closest('.noticer-item'));
});