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
            new \Twig_SimpleFilter('alphabetAuthersLinks', array($this, 'alphabetAuthersLinks'), array('is_safe' => array('html'))),

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
        $string = strip_tags($string, '<a>');

        $splitTag = explode('</a>', $string);

        $count = 0;

        $flag = false;

        $resultString = '';

        $lastSimbol = $length;

        foreach ($splitTag as $item) {
            $countItem = mb_strlen(strip_tags($item));
            $count += $countItem;

            if ($count > $length) {
                $chunk = explode('<a ', $item);

                $resultString .= substr($chunk[0], 0, $lastSimbol);
                break;
            }

            $resultString .= $item . '</a>';

            $lastSimbol -= $countItem;
        }

        if (mb_strlen($resultString) > $length && $link) {
            $resultString .= '... ' .
                '<a href="' . $link . '">' .
                $this->container->get('translator')->trans('content.link_more') .
                '</a>'
            ;
        }

        return $resultString;
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

    public function alphabetAuthersLinks($alphas)
    {
        $result = '';

        foreach ($alphas as $alpha) {

            $link = $this->container->get('router')->generate('thought_author_index', array(
                'alpha' => $alpha,
            ));

            $result .= "<a href='$link'>$alpha</a>";
        }

        return $result;
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'app_extension';
    }
}
