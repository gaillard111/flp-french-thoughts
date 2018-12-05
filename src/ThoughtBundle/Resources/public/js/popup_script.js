var modal_boot = {
    notification: function (text_header, text_body, class_window) {
        modal_boot.close_window(class_window);
        var main = modal_boot.window(text_header, text_body, class_window);
        $('div.' + class_window).modal();
    },
    confirmation: function (text_header, text_body, class_window, ok_button) {
        modal_boot.close_window(class_window);
        var main = modal_boot.window(text_header, text_body, class_window, ok_button);
        $('div.' + class_window).modal();
    },
    window : function (text_header, text_body, class_window, ok_button) {
        var main = $('<div/>').addClass('modal fade ' + class_window).appendTo('body');
        if(text_header) {
            var header = $('<div/>').addClass('modal-header').appendTo(main);
            $('<h3/>').text(text_header).appendTo(header);
        }
        var body = $('<div/>').addClass('modal-body').html(text_body).appendTo(main);
        var footer = $('<div/>').addClass('modal-footer').appendTo(main);
        if(ok_button)
        {
            $('<button/>').addClass('btn btn-info')
                .attr('type','submit')
                .attr('onclick','$("div.' + class_window + ' form").submit(); modal_boot.close_window("' + class_window + '")')
                .text('OK')
                .appendTo(footer);
        }
        $('<div/>').addClass('btn close close-button').attr('href','#').attr('onclick','modal_boot.close_window("' + class_window + '")').text('Close').appendTo(footer);
    },
    close_window : function (class_window) {
        var div = $('div.' + class_window);
        div.next('div').remove();
        div.remove();
        $('body').removeClass('modal-open');
    }
};