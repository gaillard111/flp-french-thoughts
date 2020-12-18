var HasTooltip = $('.hastooltip');
HasTooltip.on('click', function(e) {
    e.preventDefault();
    var isShowing = $(this).data('isShowing');
    HasTooltip.removeData('isShowing');
    if (isShowing !== 'true')
    {
        HasTooltip.not(this).tooltip('hide');
        $(this).data('isShowing', "true");
        $(this).tooltip('show');
    }
    else
    {
        $(this).tooltip('hide');
    }

}).tooltip({
    animation: true,
    trigger: 'manual'
});

 $(".chains-selector .chain").click(function () {
     var $this = $(this);
    if (!$this.hasClass('disabled')) {
        var $chain = $this.attr('id');
        var $quote = $this.closest("div[id^='thought-']").attr('id');
        if ($chain && $quote) {
            $.ajax({
                url: Routing.generate('chain_add_quote'),
                data: {
                    quote: $quote,
                    chain: $chain
                },
                dataType: "json",
                success: function (data) {
                    if (data.success) {
                        noticer.success(data.message[0]);
                        $this.addClass('disabled');
                    } else {
                        var error = '';
                        $.each(data.message, function (k, v) {
                            error += '<p>' + v + '</p>';
                        })
                        noticer.alert(error);
                    }
                }
            });
        }
    }
 });

$(".send_id_for_related").click(function () {
    var $this = $(this);
    const action = Routing.generate('link-quotes');
    let data = $this.parent().serialize();
    $.ajax({
        type: 'POST',
        url: action,
        data: data,
        success: function (response) {
            if (response.success) {
                noticer.success(response.message);
            } else {
                noticer.alert(response.message);
            }
        }
    });
});

 $('span.author a').mouseover(function(){
     $(this).parents('div.quote').find('div.authors_info').fadeIn();
 }).mouseout(function(){
     $(this).parents('div.quote').find('div.authors_info').fadeOut();
 });



