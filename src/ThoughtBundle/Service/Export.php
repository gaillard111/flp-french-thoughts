<?php

namespace ThoughtBundle\Service;

use Symfony\Component\HttpFoundation\Response;

/**
 * Class Export
 * @package ThoughtBundle\Service
 */
class Export
{
    /**
     * @param array  $thoughts
     * @param string $filename
     * @return Response
     */
    public function exportThoughts($thoughts)
    {
        $string = '';
        foreach ($thoughts as $thought) {
            $string .= html_entity_decode('&laquo;') . '[' . $thought->getId() . ']' .
                $thought->getContent() . html_entity_decode('&raquo;') .
                ' ' . $thought->getAuthor();

            if (!empty($thought->getThoughtInfo())) {
                $string .= ', ' . $thought->getThoughtInfo();
            }

            $string .= ' - ' . $thought->getCategory();

            if (!empty($thought->getTags())) {
                $string .= ' - ' . implode(' - ', explode(',', $thought->getTags()));
            }

            $string .= "\r\n";
        }

        $string = mb_convert_encoding($string, 'iso-8859-1', 'utf-8');

        $filename = 'export_thought_' . date('Y_m_d_H_i_s', strtotime('now')) . '.txt';

        $response = new Response($string, 200, array(
            'Content-Type'        => 'plain/text; charset=ASCII',
            'Content-Disposition' => 'attachment; filename="' . $filename . '"',
        ));

        return $response;
    }
}