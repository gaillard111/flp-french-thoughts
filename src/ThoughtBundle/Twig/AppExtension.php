<?php

namespace ThoughtBundle\Twig;

/**
 * Class AppExtension
 * @package ThoughtBundle\Twig
 */
class AppExtension extends \Twig_Extension
{
    /**
     * @return array
     */
    public function getFilters()
    {
        return array(
            new \Twig_SimpleFilter('customTag', array($this, 'customTagFilter')),
        );
    }

    /**
     * @param string $string
     * @return mixed
     */
    public function customTagFilter($string)
    {
        $pattern = '/(?<=\[a )(.*)(?=\[\/a])/U';

        $parts = explode('[a ', $string);

        foreach ($parts as $key => $part) {
            if ($key) {
                preg_match_all($pattern, '[a ' . $part, $match);

                foreach ($match[0] as $item) {
                    $subString = explode(']', $item);

                    if (count($subString) == 2) {
                        $string = str_replace('[a ' . $item . '[/a]', '<a href="' . $subString[0] .'">' . $subString[1] . '</a>', $string);
                    }
                }
            }
        }

        return $string;
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'app_extension';
    }
}
