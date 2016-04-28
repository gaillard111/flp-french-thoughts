<?php

namespace ThoughtBundle\Parser;

use Symfony\Component\DependencyInjection\Container;
use Symfony\Component\HttpFoundation\File\UploadedFile;

/**
 * Class Service
 * @package ParseBundle\Parser
 */
class Service
{
    /**
     * @var Container
     */
    private $container;

    /**
     * Service constructor.
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->container = $container;
    }

    /**
     * @param UploadedFile $file
     * @return int
     */
    public function parseFile(UploadedFile $file)
    {
        $filePath = $file->getPathname();

        $data = array();

        $content = file_get_contents($filePath);

        $encoding = mb_detect_encoding($filePath);

        $content = mb_convert_encoding($content, 'utf-8', $encoding);

        $quotes = explode(html_entity_decode('&laquo;'), htmlspecialchars($content));

        foreach ($quotes as $key => $quote) {
            $quoteCategory = '';
            $quoteAuthor = '';
            $quoteInfo = '';
            $quoteTags = '';
            $parseString = '';

            $quoteParts = explode(html_entity_decode('&raquo;'), $quote);

            $quoteContent = trim($quoteParts[0]);

            preg_match('/\[\d+\]/', $quoteContent, $match);
            $quoteContent = preg_replace('/\[\d+\]/', '', $quoteContent);

            $id = isset($match[0]) ? trim($match[0], '[]') : null;


            if (isset($quoteParts[1])) {
                $parseString = trim($quoteParts[1]);

                $parseStringParts = explode(',', $parseString);

                if (count($parseStringParts) == 1) {
                    $parseStringParts = explode(' - ', $parseString);

                    $quoteAuthor = trim($parseStringParts[0]);

                    unset($parseStringParts[0]);

                    $parseStringParts = implode(' - ', $parseStringParts);

                    $parseStringParts = explode(' - ', $parseStringParts);

                    $quoteCategory = $parseStringParts[0];

                    if (count($parseStringParts) > 1) {
                        unset($parseStringParts[0]);

                        $quoteTags = implode(', ', $parseStringParts);
                    }

                } else {
                    $quoteAuthor = trim($parseStringParts[0]);

                    unset($parseStringParts[0]);

                    $parseStringParts = implode(',', $parseStringParts);

                    $parseStringParts = explode(' - ', $parseStringParts);

                    $quoteInfo = $parseStringParts[0];

                    if (count($parseStringParts) > 1) {
                        $quoteCategory = $parseStringParts[1];

                        unset($parseStringParts[0]);
                        unset($parseStringParts[1]);

                        $quoteTags = implode(',', $parseStringParts);
                    }
                }
            }

            $data[] = array(
                'id'        => $id,
                'content'   => $quoteContent,
                'author'    => $quoteAuthor,
                'info'      => $quoteInfo,
                'category'  => $quoteCategory,
                'tags'      => $quoteTags,
                'string'    => $parseString,
                'published' => true,
            );
        }

        return $this->container->get('thought.model.thought_model')->saveThoughts($data);
    }
}
