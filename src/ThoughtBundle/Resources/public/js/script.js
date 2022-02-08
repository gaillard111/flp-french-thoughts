$(function() {
    $('[data-toggle="tooltip"]').tooltip();

    $('.jumbotron .like-quote').on('click', function(e){
        e.preventDefault();
        var button = $(this),
            badge = button.find('span.badge'),
            badgeText = button.find('span.badge-text'),
            quoteId = button.data('quote');

        $.ajax({
            url : Routing.generate('thought-like') + '/' + quoteId,
            dataType: "json",
            success: function(data) {
                badge.text(data.count);

                if (data.count > 0) {
                    badge.css('display', 'inline-block');
                } else {
                    badge.hide();
                }

                if (data.count == 'added') {
                    badgeText.text('Aimé');
                } else {
                    badgeText.text("J'aime");
                }
            }
        });
    });

    $('.jumbotron .add_chain').on('click', function(e){
        e.preventDefault();

        var chain = $(this).closest('.quote_chain').find('[name="quote_chain"]').val(),
            quote = $(this).closest('.jumbotron').data('quote');

        $.ajax({
            url : Routing.generate('chain_add_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.jumbotron .add_collective_chain').on('click', function(e){
        e.preventDefault();

        var chain = $(this).closest('.quote_chain').find('[name="quote_collective_chain"]').val(),
            quote = $(this).closest('.jumbotron').data('quote');

        $.ajax({
            url : Routing.generate('chain_add_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-quote-control a.chain-quote-remove').on('click', function(e){
        e.preventDefault();

        var $quoteElem = $(this).closest('.chain-quote-block'),
            $blockControl = $(this).closest('.chain-quote-control'),
            quote = $blockControl.data('target'),
            chain = $blockControl.data('chain-id')
        ;

        $.ajax({
            url : Routing.generate('chain_remove_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    $quoteElem.remove();

                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-quote-control a.chain-quote-upper').on('click', function(e){
        e.preventDefault();

        var $quoteElem = $(this).closest('.chain-quote-block'),
            $blockControl = $(this).closest('.chain-quote-control'),
            quote = $blockControl.data('target'),
            chain = $blockControl.data('chain-id')
        ;

        $.ajax({
            url : Routing.generate('chain_upper_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    $quoteElem.detach().prependTo('.chain-quote-wrapper');

                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-quote-control a.chain-quote-lower').on('click', function(e){
        e.preventDefault();

        var $quoteElem = $(this).closest('.chain-quote-block'),
            $blockControl = $(this).closest('.chain-quote-control'),
            quote = $blockControl.data('target'),
            chain = $blockControl.data('chain-id')
        ;

        $.ajax({
            url : Routing.generate('chain_lower_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    $quoteElem.detach().appendTo('.chain-quote-wrapper');

                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-quote-control a.chain-quote-up').on('click', function(e){
        e.preventDefault();

        var $quoteElem = $(this).closest('.chain-quote-block'),
            $blockControl = $(this).closest('.chain-quote-control'),
            quote = $blockControl.data('target'),
            chain = $blockControl.data('chain-id'),
            $sibling = $quoteElem.prev('.chain-quote-block')
            ;

        $.ajax({
            url : Routing.generate('chain_up_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    $quoteElem.detach().insertBefore($sibling);

                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-quote-control a.chain-quote-down').on('click', function(e){
        e.preventDefault();

        var $quoteElem = $(this).closest('.chain-quote-block'),
            $blockControl = $(this).closest('.chain-quote-control'),
            quote = $blockControl.data('target'),
            chain = $blockControl.data('chain-id'),
            $sibling = $quoteElem.next('.chain-quote-block')
            ;

        $.ajax({
            url : Routing.generate('chain_down_quote'),
            data: {
                quote: quote,
                chain: chain
            },
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    $quoteElem.detach().insertAfter($sibling);

                    noticer.success(data.message[0]);
                } else {
                    var error = '';
                    $.each(data.message, function(k, v){
                        error += '<p>' + v + '</p>';
                    });

                    noticer.alert(error);
                }
            }
        });
    });

    $('.chain-list .chain-remove').on('click', function(e){
        e.preventDefault();

        var link = $(this).attr('href'),
            body = '<form action="' + link + '">Are you sure you want to delete it?</form>';

        modal_boot.confirmation('Confirmation', body, 'confirm-remove-chain', true);
    });
});
