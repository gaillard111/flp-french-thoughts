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

function buttonToggle(source, target, show_val, hide_val, input) {

    if (target.offsetWidth === 0 && target.offsetHeight === 0) {
        target.style.display = 'block';
    } else {
        target.style.display = 'none';
    }
}

document.getElementById('advanced_search_button').onclick = (function() {
    var table = document.getElementById('advanced_search_block');
    return function() {
        buttonToggle(this, table, 'View', 'Hide');
    };
}());

document.getElementById('1_search_button').onclick = (function() {
    var table = document.getElementById('1_search_block');
    return function() {
        buttonToggle(this, table, 'View', 'Hide');
    };
}());

document.getElementById('2_search_button').onclick = (function() {
    var table = document.getElementById('2_search_block');
    return function() {
        buttonToggle(this, table, 'View', 'Hide');
    };
}());

document.getElementById('3_search_button').onclick = (function() {
    var table = document.getElementById('3_search_block');
    return function() {
        buttonToggle(this, table, 'View', 'Hide');
    };
}());

if (document.getElementById('filters_button')) {
    document.getElementById('filters_button').onclick = (function() {
        var table = document.getElementById('filters_block');
        var filterOpen = document.getElementById('filter_block_open');

        return function() {
            filterOpen.getAttribute('value') == '1' ? filterOpen.setAttribute('value', '0') : filterOpen.setAttribute('value', '1');
            buttonToggle(this, table, 'View', 'Hide', filterOpen);
        };
    }());
}

$(document).on('click', "#cloud_button", function () {
    var $cloudBlock = $("#cloud_block");

    if ($cloudBlock.hasClass("hidden")) {
        $cloudBlock.removeClass("hidden");
    } else {
        $cloudBlock.addClass("hidden");
    }
});


$(document).ready(function() {

    $(this).scroll(function () {
        var $menu = $('.fixed-menu');

        if ($(window).scrollTop() >= 300) {
            $menu.css('position', 'fixed');
            $menu.css('top', '20px');
        }
        if ($(window).scrollTop() <= 300) {
            $menu.css('position', '');
            $menu.css('top', '');
        }
    });

    if (!$("#inputSearch").val()) {
        $('#myModal').modal('show');
    }
    $('#commentModal').modal('show');
    $('#newThoughtModal').modal('show');

    $('span.author a').mouseover(function(){
        $(this).parents('div.quote').find('div.authors_info').fadeIn();
    }).mouseout(function(){
        $(this).parents('div.quote').find('div.authors_info').fadeOut();
    });

    $('.show-link').click(function () {
        var $btn = $(this);
        var thoughtId = $btn.data('id');
        var $element = $('.comments[data-id=' + thoughtId + ']');
        if ($element.hasClass('hidden')) {
            $element.removeClass('hidden');
        } else {
            $element.addClass('hidden');
        }
    });

    $(".related-thoughts-label").click(function () {
        var $this = $(this);
        var $relatedThoughts = $this.next();

        if ($relatedThoughts.is(":hidden")) {
            $relatedThoughts.css('display', 'flex');
        } else {
            $relatedThoughts.hide();
        }

    });

    // $(window).focus(function () {
    setInterval(function () {
        $.ajax({
            url:        "{{ path('ajax_counter') }}",
            method:     "POST",
            success:    function (data) {
                console.log(data);
                $("#messages-counter").html('(+' + data['count'][1] + ')');
            }
        });
    }, 30000);
    // });

    $("input[name='search[author][envjc]']").click(function () {
        let $birthDateField = $("input[name='search[author][birthDate]']");

        if($birthDateField.attr('disabled') !== 'disabled') {
            $birthDateField.attr('disabled', 'disabled');
        } else {
            $birthDateField.removeAttr('disabled');
        }
    });

});