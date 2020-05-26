<?php

namespace ThoughtBundle\Twig;

use Collator;
use Exception;
use FOS\ElasticaBundle\Finder\FinderInterface;
use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Author;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\ThoughtChain;
use ThoughtBundle\Model\AuthorModel;
use Twig_SimpleFilter;

/**
 * Class AppExtension
 *
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
     *
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
        return [
            new Twig_SimpleFilter('customTag', [$this, 'customTagFilter']),
            new Twig_SimpleFilter('shortText', [$this, 'customShortText']),
            new Twig_SimpleFilter('alphabetAuthersLinks', [$this, 'alphabetAuthersLinks'], ['is_safe' => ['html']]),
            new Twig_SimpleFilter('authorsInfo', [$this, 'authorsInfo']),
            new Twig_SimpleFilter('asort', [$this, 'asort']),
            new Twig_SimpleFilter('some_sort_filter', [$this, 'some_sort_filter']),
        ];
    }

    public function asort($array)
    {
        usort($array, function ($elem1, $elem2) {
            /**
             * @var Chain $elem1
             * @var Chain $elem2
             */
            setlocale(LC_COLLATE, 'fr_FR');
            return strcoll($elem1->getName(), $elem2->getName());
        });
        return $array;
    }

    public function some_sort_filter($array)
    {   /** @var ThoughtChain[] $array */
        usort($array, function ($elem1, $elem2) {
            /**
             * @var ThoughtChain $elem1
             * @var ThoughtChain $elem2
             */
            return strcmp($elem1->getThought()->getCategory(), $elem2->getThought()->getCategory());
        });

        return $array;
    }

    /**
     * @param string $string
     * @param int    $length
     * @param string $link
     *
     * @return string
     *
     * @throws Exception
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
     *
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
                        $string = str_replace('[a ' . $item . '[/a]', '<a href="' . $subString[0] . '">' . $subString[1] . '</a>', $string);
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
            $link = $this->container->get('router')->generate('thought_author_index', [
                'alpha' => $alpha,
            ]);

            $result .= "<a href='$link'>$alpha</a>";
        }

        return $result;
    }

    public function authorsInfo($name)
    {
        /** @var FinderInterface $authorsFinder */
        $authorsFinder = $this->container->get('fos_elastica.finder.app.author');

        /** @var AuthorModel $authorModel */
        $authorModel = $this->container->get('thought.model.author_model');

        $authors = $authorsFinder->find($authorModel->searchDefault($name));

        if (!isset($authors[0])) {
            return null;
        }

        /** @var Author $author */
        return $authors[0];
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'app_extension';
    }
}
