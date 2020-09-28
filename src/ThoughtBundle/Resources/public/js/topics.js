let $topicLink = $(".topic-link a");
let $chainLink = $(".chain-link a");


$topicLink.click(function () {
    let $this = $(this).parent();
    let $chainsBlock = $this.children(".chain-list");
    let $chainLinks = $this.children(".chain-list").children(".chain-link");

    if ($chainsBlock.css('display') === 'none' && $chainLinks.length > 0) {
        $chainsBlock.css('display', 'block');
    } else {
        $chainsBlock.css('display', 'none');
    }
});

$chainLink.click(function (event) {
    let $this = $(this).parent();
    let $quotesBlock = $this.children(".quote-list");
    let $quoteLinks = $this.children(".quote-list").children(".quote-link")

    if ($quotesBlock.css('display') === 'none' && $quoteLinks.length > 0) {
        $quotesBlock.css('display', 'flex');
    } else {
        $quotesBlock.css('display', 'none');
    }
});