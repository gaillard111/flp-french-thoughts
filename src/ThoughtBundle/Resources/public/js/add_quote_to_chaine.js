 $(".chains-selector .chain").click(function () {   var $this = $(this);
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