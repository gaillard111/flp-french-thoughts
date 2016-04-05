<?php

namespace ThoughtBundle\Parser;

/**
 * Class Service
 * @package ParseBundle\Parser
 */
class Service
{
    public function testParse()
    {
        $filePath = __DIR__ . '/parseTxt.txt';

        $content = file_get_contents($filePath);

        $encoding = mb_detect_encoding($filePath);

        $content = mb_convert_encoding($content, 'utf-8', $encoding);

        $quotes = explode(html_entity_decode('&laquo;'), htmlspecialchars($content));

        echo '<pre>';
        var_dump($quotes[1]);
        echo '</pre>';
    }
}