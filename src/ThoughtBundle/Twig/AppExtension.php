<?php

namespace ThoughtBundle\Twig;
use Symfony\Component\DependencyInjection\Container;

/**
 * Class AppExtension
 * @package ThoughtBundle\Twig
 */
class AppExtension extends \Twig_Extension
{
    /**
     * @var Container
     */
    private $container;

    /**
     * AppExtension constructor.
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->container = $container;
    }

    /**
     * @return array
     */
    public function getFilters()
    {
        return array(
            new \Twig_SimpleFilter('customTag', array($this, 'customTagFilter')),
            new \Twig_SimpleFilter('shortText', array($this, 'customShortText')),

        );
    }

    /**
     * @param string $string
     * @param int    $length
     * @param string $link
     * @return string
     */
    public function customShortText($string, $length = 1, $link = null)
    {
        $words = explode(' ', strip_tags($string));

        $countLetters = 0;

        foreach ($words as $key => $word) {
            $countLetters += mb_strlen($word) + 1;

            if ($countLetters > $length) {
                $words = array_slice($words, 0, $key + 1);

                break;
            }
        }

        $string = implode(' ', $words);

        if ($countLetters > $length && $link) {
            $string .= '... ' .
                '<a href="' . $link . '">' .
                $this->container->get('translator')->trans('content.link_more') .
                '</a>'
            ;
        }

        return $string;
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
