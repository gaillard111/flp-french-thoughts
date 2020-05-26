function redirect(selector) {
    $(selector).click(function (event) {
        event.stopPropagation();
        event.preventDefault();
        let $this = $(this);
        window.location.href = $this.attr('href');
    });
}

let $topicLink = $(".topic-link");
let $chainLink = $(".chain-link");

$topicLink.hover(function () {
    let $this = $(this);
    let $chainLinks = $this.children(".chain-list").children(".chain-link");

    if ($chainLinks.length === 0) {
        $this.children('a').css('cursor', 'default');
        $this.children('a').css('color', '#337ab7');
        $this.children('a').css('text-decoration', 'none');
    }
});

$chainLink.hover(function () {
    let $this = $(this);
    let $quoteLinks = $this.children(".quote-list").children(".quote-link");

    if ($quoteLinks.length === 0) {
        $this.children('a').css('cursor', 'default');
        $this.children('a').css('color', '#337ab7');
        $this.children('a').css('text-decoration', 'none');
    }
});

$chainLink.click(function (event) {
    event.stopPropagation();
    event.preventDefault();
    let $this = $(this);
    let chainId = $this.data('chain');
    let $quoteList = $(".quote-list[data-chain=" + chainId + "]");

    if ($this.children(".quote-list").children(".quote-link").length === 0) {
        return;
    }

    if ($quoteList.css('display') === 'none') {
        $quoteList.css('display', 'flex');
    } else {
        $quoteList.hide();
    }
});

$topicLink.click(function (event) {
    event.stopPropagation();
    event.preventDefault();
    let $this = $(this);
    let topicId = $this.data('topic');
    let $chainList = $(".chain-list[data-topic=" + topicId + "]");
    let $chainLinks = $this.children(".chain-list").children(".chain-link");

    if ($this.hasClass("topic-link-empty")) {
        return;
    }

    if ($chainLinks.length === 0) {
        return;
    }

    if ($chainList.css('display') === 'none') {
        $chainList.css('display', 'flex');
    } else {
        $chainList.hide();
    }
});

redirect(".open-chain");
redirect(".quote-link");