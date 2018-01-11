<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Elastica\Query;
use FOS\ElasticaBundle\Finder\FinderInterface;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtModel
 * @package ThoughtBundle\Model
 */
class ThoughtModel
{
    const CLOUD_MIN_FONT_SIZE   = 15;
    const CLOUD_MIN_FONT_WEIGHT = 200;
    const CLOUD_NUMBER_OF_WORDS = 30;

    /**
     * @var EntityManager
     */
    protected $em;

    /**
     * @var Container
     */
    protected $container;

    /**
     * @var \Doctrine\ORM\EntityRepository
     */
    protected $repository;

    /**
     * ThoughtModel constructor.
     * @param EntityManager $em
     * @param Container     $container
     */
    public function __construct(EntityManager $em, Container $container)
    {
        $this->em         = $em;
        $this->container  = $container;
        $this->repository = $em->getRepository('ThoughtBundle:Thought');
    }

    /**
     * @return \Doctrine\ORM\Query
     */
    public function getThoughts()
    {
        return $this->repository->createQueryBuilder('t')
            ->where('t.published = 1')
            ->orderBy('t.createdAt', 'DESC')
            ->getQuery();
    }

    /**
     * @param User $user
     * @return \Doctrine\ORM\Query
     */
    public function getUserThoughts(User $user)
    {
        return $this->repository->createQueryBuilder('t')
            ->where('t.owner = :user')
            ->orderBy('t.createdAt', 'DESC')
            ->setParameter('user', $user)
            ->getQuery();
    }

    /**
     * @param array             $request
     * @param TransformedFinder $finder
     * @return \Doctrine\ORM\Query|\FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface|\FOS\ElasticaBundle\Paginator\TransformedPaginatorAdapter
     */
    public function getThoughtsFromElastic($request, TransformedFinder $finder, TransformedFinder $authorsFinder)
    {
        $fields = array(
            'tags',
            'author',
            'content',
            'category',
            'thoughtInfo',
        );

        if (isset($request['field']) and  count($request['field']) > 0) {
            $fields = array_keys($request['field']);
        }

        $isAuthor = false;
        $terms = array();

        if (isset($request['author']) and count($request['author']) > 0) {
            foreach ($request['author'] as $key => $val) {
                if ($val) {

                    $isAuthor = true;

                    $val = trim($val);

                    $countQuote = explode('"', $val);

                    if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
                        $val = $countQuote[1];

                        $terms[] = array(
                            'query' => array(
                                'term' => array(
                                    $key . '_exact' => $val,
                                )
                            )
                        );

                    } else {
                        $terms[] = array(
                            'query' => array(
                                'multi_match' => array(
                                    'query'                => $val,
                                    'fields'               => array(
                                        $key
                                    ),
                                    'minimum_should_match' => '100%',
                                    'type'                 => 'cross_fields',
                                    'operator'             => 'and',
                                    'tie_breaker'          => '1.0',
                                    'analyzer'             => 'standard',
                                ),
                            )
                        );
                    }
                }
            }
        }

        $names = [];

        $time_start = microtime(true);

        if ($isAuthor) {
            $names = $this->getNames($terms, $authorsFinder);
        }

        $time_end = microtime(true);
        $time = $time_end - $time_start;



        if (isset($request['term']) and count($request['term']) > 0) {

            $terms = array();

            foreach ($request['term'] as $key => $val) {
                if ($val) {
                    $val = trim($val);

                    $countQuote = explode('"', $val);

                    if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
                        $terms[] = array(
                            'query' => array(
                                'match_phrase' => array(
                                    $key . '_phrase' => $val,
                                )
                            )
                        );
                    } else {
                        $terms[] = array(
                            'query' => array(
                                'match' => array(
                                    $key . '_phrase' => $val,
                                )
                            )
                        );
                    }
                }
            }
        }

        if ($isAuthor) {
            $terms[] = array(
                'terms' => array(
                    'author_exact' => $names,
                )
            );
        }

        $sort = array(
            'amount' => 'asc'
        );

        if (isset($request['sorting']) && $request['sorting']) {
            $sort = array(
                $request['sorting'] => (isset($request['sorting_desc']) ? 'desc' : 'asc'),
            );
        }

        $strict = (isset($request['strict']) && $request['strict']) ? true : false;

        $maxWords = (isset($request['max_words']) && $request['max_words'] > 0) ? intval($request['max_words']) : 99999999;

        $minWords = isset($request['min_words']) ? intval($request['min_words']) : 0;

        $minChars = isset($request['min_chars']) ? intval($request['min_chars']) : 0;

        $words = (isset($request['words']) && mb_strlen($request['words']) > 0) ? trim($request['words']) : null;

        $lastChar = $words[mb_strlen($words) - 1];

        $words = ($lastChar == ',' || $lastChar == '.' || $lastChar == '!') ? mb_substr($words, 0, -1) : $words;

        $countQuote = explode('"', $words);

        if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
            $query = $this->searchQuoteString($countQuote[1], $fields, $minWords, $maxWords, $sort, $terms);

            $thoughts = $finder->createPaginatorAdapter($query);

            return $thoughts;
        }

        $arrWords = explode(' ', $words);

        $wordExceptions = array();

        foreach ($arrWords as $keyArrWords => $valueArrWords) {
            if (!empty($valueArrWords)) {
                if ($valueArrWords[0] == '-') {
                    $wordExceptions[] = $this->filterWord($valueArrWords);
                    unset($arrWords[$keyArrWords]);
                }
            }
        }

        $words = implode(' ', $arrWords);

        $filterException = $this->compileExceptions($fields, $wordExceptions);

        if ($words) {
            if ($strict) {
                $query = $this->searchExactly($words, $fields, $minWords, $maxWords, $sort);
            } else {
                $words = $this->filterWord($words);

                if (count(explode(' ', $words)) > 1) {
                    $query = $this->searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms);
                } else {
                    $query = $this->searchWord($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms);
                }
            }
        } else {
            $query = $this->searchDefault($minWords, $maxWords, $sort, $filterException, $terms);
        }

        $thoughts = $finder->createPaginatorAdapter($query);

        return $thoughts;
    }

    /**
     * @param array $data
     * @return int
     */
    public function saveThoughts(array $data)
    {
        $flag = false;

        $countAdded = 0;

        $transactionNum = 0;

        foreach ($data as $item) {
            if ($this->createTransaction($item)) {
                $flag = true;
                $countAdded++;
                $transactionNum++;

                if ($transactionNum % 100 == 0) {
                    $this->em->flush();
                }
            }
        }

        if ($flag == true) {
            $this->em->flush();
        }

        return $countAdded;
    }

    /**
     * @param Thought $thought
     * @return Thought
     */
    public function addLike(Thought  $thought)
    {
        $thought->setLiked($thought->getLiked() + 1);

        $this->em->persist($thought);
        $this->em->flush();

        return $thought;
    }

    /**
     * @param Thought $thought
     * @return Thought
     */
    public function removeLike(Thought  $thought)
    {
        $thought->setLiked($thought->getLiked() - 1);

        $this->em->persist($thought);
        $this->em->flush();

        return $thought;
    }

    /**
     * @param array $filters
     * @param array $filterFields
     * @return array
     */
    public function getFilteredThoughts(array $filters, array $filterFields)
    {
        $where     = array();
        $sortBy    = null;
        $sortOrder = null;

        if (count($filters)) {
            $sortBy = isset($filters['_sort_by']) ? $filters['_sort_by'] : null;
            $sortOrder = isset($filters['_sort_order']) ? $filters['_sort_order'] : null;

            foreach ($filters as $filterName => $filterParams) {
                if (in_array($filterName, $filterFields)) {
                    switch ($filterParams['type']) {
                        case 1:
                            $where[$filterName] = " LIKE '%" . $filterParams['value'] . "%'";
                            break;
                        case 2:
                            $where[$filterName] = " NOT LIKE '%" . $filterParams['value'] . "%'";
                            break;
                        case 3:
                            $where[$filterName] = " = '" . $filterParams['value'] . "'";
                            break;
                    }
                }
            }
        }

        return $this->repository->getFilterThoughts($where, $sortOrder, $sortBy);
    }

    /**
     * @param string $words
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     * @return $this
     */
    public function searchExactly($words, $fields, $minWords, $maxWords, $sort)
    {
        $query = new \Elastica\Query();

        $arrFields = array();

        foreach ($fields as $field) {

            $arrFields[] = array(
                'bool' => array(
                    'must' => array(
                        'term' => array(
                            ($field . '_exact') => $words,
                        ),
                    ),
                ),
            );
        }

        $arr = array(
            'filter' => array(
                'bool' => array(
                    'should' => $arrFields,
                    'must' => array(
                        'range' => array(
                            'amount' => array(
                                'gte' => $minWords,
                                'lte' => $maxWords,
                            ),
                        ),
                    ),
                ),
            ),
            'sort' => $sort,
        );

        return $query->setParams($arr);
    }

    /**
     * @param string $words
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     * @param array  $filterException
     * @return $this
     */
    public function searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms)
    {
        $query = new \Elastica\Query();

        $must = array(
            array(
                'range' => array(
                    'amount' => array(
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ),
                ),
            ),
        );

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query->setParams(
            array(
                'query' => array(
                    'multi_match' => array(
                        'query'                => $words,
                        'fields'               => $fields,
                        'minimum_should_match' => '100%',
                        'type'                 => 'cross_fields',
                        'operator'             => 'and',
                        'tie_breaker'          => '1.0',
                        'analyzer'             => 'standard',
                    ),
                ),
                'filter' => array(
                    'bool' => array(
                        'must_not' => $filterException,
                        'must' => $must
                    ),
                ),
                'sort' => $sort,
            )
        );

        return $query;
    }

    /**
     * @param string $words
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     * @param array  $filterException
     * @return Query
     */
    public function searchWord($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms)
    {
        $must = array(
            array(
                'range' => array(
                    'amount' => array(
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ),
                ),
            ),
        );

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query = new \Elastica\Query();
        $query->setParams(
            array(
                'query' => array(
                    'multi_match' => array(
                        'query'                => $words,
                        'fields'               => $fields,
                        'operator'             => 'and',
                        'minimum_should_match' => '100%',
                    ),
                ),
                'filter' => array(
                    'bool' => array(
                        'must_not' => $filterException,
                        'must' => $must,
                    ),
                ),
                "sort" => $sort
            )
        );

        return $query;
    }

    /**
     * @param int   $minWords
     * @param int   $maxWords
     * @param array $sort
     * @param array $filterException
     * @return Query
     */
    public function searchDefault($minWords, $maxWords, $sort, $filterException, $terms)
    {
        $must = array(
            array(
                'range' => array(
                    'amount' => array(
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ),
                ),
            ),
        );

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query = new \Elastica\Query();

        $query->setRawQuery(
            array(
                'filter' => array(
                    'bool' => array(
                        'must_not' => $filterException,
                        'must' => $must
                    ),
                ),
                'sort' => $sort,
            )
        );

        return $query;
    }

    /**
     * @param string $string
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     * @return $this|Query
     */
    public function searchQuoteString($string, $fields, $minWords, $maxWords, $sort, $terms)
    {
        $query = new \Elastica\Query();

        $must = array(
            array(
                'range' => array(
                    'amount' => array(
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ),
                ),
            ),
        );

        if (!empty($terms)) {
            $must[] = $terms;
        }

        if (count(explode(' ', $string)) > 1) {
            $phraseFields = array();

            foreach ($fields as $field) {
                $phraseFields[] = $field . '_phrase';
            }

            $query->setParams(
                array(
                    'query' => array(
                        'multi_match' => array(
                            'query'                => $string,
                            'fields'               => $phraseFields,
                            'operator'             => 'and',
                            'minimum_should_match' => '100%',
                            'type'                 => 'phrase',
                        ),
                    ),
                    'filter' => array(
                        'bool' => array(
                            'must' => $must
                        ),
                    ),
                    'sort' => $sort,
                )
            );

            return $query;
        }

        $arrFields = array();

        foreach ($fields as $field) {
            $arrFields[] = array(
                'prefix' => array(
                    ($field . '_phrase') => $string,
                ),
            );
        }

        $arr = array(
            'filter' => array(
                'bool' => array(
                    'should' => $arrFields,
                    'must' => $must
                ),
            ),
            'sort' => $sort,
        );

        return $query->setParams($arr);
    }

    public function getLastThoughts($limit) {
        return $this->repository->findBy(array(), array('createdAt' => 'DESC'), $limit);
    }

    /**
     * @param array $fields
     * @param PaginatorAdapterInterface $thoughts
     *
     * @return array
     */
    public function getCloud($fields, $thoughts, $words) {
        $cloud = $cloudStyle = [];

        if (!is_array($thoughts) && $words) {

            if ($thoughts->getTotalHits() > 0) {
                $cloud = [];
                $cloudContent = [];

                /** @var Thought $thought */
                foreach ($thoughts->getResults(0, $thoughts->getTotalHits())->toArray() as $thought) {

                    $tags = explode(',', $thought->getTags());
                    $words = explode(' ', $thought->getContent());

                    if (count($words) <= 80) {
                        foreach ($words as $word) {
                            if (mb_strlen(trim(strtolower($word))) >= 5) {
                                if (!isset($cloudContent[trim(strtolower($word))])) {
                                    $cloudContent[trim(strtolower($word))] = 0;
                                }

                                $cloudContent[trim(strtolower($word))]++;
                            }
                        }
                    }


                    foreach ($tags as $tag) {
                        if (!$tag || mb_strlen(trim(strtolower($tag))) < 5) {
                            continue;
                        }

                        if (!isset($cloud[trim(strtolower($tag))])) {
                            $cloud[trim(strtolower($tag))] = 0;
                        }

                        $cloud[trim(strtolower($tag))]++;
                    }

                    if (!$thought->getCategory()) {
                        continue;
                    }

                    if (!isset($cloud[trim(strtolower($thought->getCategory()))])) {
                        //$cloud[trim(strtolower($thought->getCategory()))] = 0;
                    }

                    //$cloud[trim(strtolower($thought->getCategory()))]++;
                }
            }

            array_multisort($cloud, SORT_DESC);
            array_multisort($cloudContent, SORT_DESC);


            $cloud        = array_slice($cloud, 0, self::CLOUD_NUMBER_OF_WORDS/2);
            $cloudContent = array_slice($cloudContent, 0, self::CLOUD_NUMBER_OF_WORDS/2);

            $cloud = array_merge($cloud, $cloudContent);

            ksort($cloud);

            foreach ($cloud as $word => $count) {
                if (!isset($cloudStyle[$word])) {
                    $cloudStyle[$word]                = [];
                    $cloudStyle[$word]['font-size']   = 0;
                    $cloudStyle[$word]['font-weight'] = 0;
                }

                $cloudStyle[$word]['font-size']   = $this->cloudFontSize($cloud[$word]);
                $cloudStyle[$word]['font-weight'] = $this->cloudFontWeight($cloud[$word]);
            }
        }

        return [
            'cloud'      => $cloud,
            'cloudStyle' => $cloudStyle
        ];
    }

    /**
     * return value of font-size depends on popularity
     *
     * @param $val
     * @return int
     */
    private function cloudFontSize($val) {
        return self::CLOUD_MIN_FONT_SIZE + sqrt($val);
    }

    /**
     * return value of font-weight depends on popularity
     *
     * @param $val
     * @return int
     */
    private function cloudFontWeight($val) {

        $weight = ceil((self::CLOUD_MIN_FONT_WEIGHT * sqrt($val)/100))*100;

        return $weight > 900 ? 900 : $weight;
    }

    /**
     * @param string $word
     * @return string
     */
    private function filterWord($word)
    {
        $word = preg_replace('/\'/', '', $word);
        $word = preg_replace('/\-/', '', $word);

        return $word;
    }

    /**
     * @param array $fields
     * @param array $words
     * @return array
     */
    private function compileExceptions($fields, $words)
    {
        $result = array();

        if (count($words)) {
            foreach ($fields as $field) {
                $arrWords = array();

                foreach ($words as $word) {
                    $arrWords[] = array(
                        'term' => array(
                            $field => $word,
                        ),
                    );
                }

                $result[] = $arrWords;
            }
        }

        return $result;
    }

    /**
     * @param array $data
     * @return bool|int
     */
    private function createTransaction(array $data)
    {
        $thought = null;

        $id = (isset($data['id'])) ? $data['id'] : null;
        $tags = (isset($data['tags'])) ? $data['tags'] : null;
        $author = (isset($data['author'])) ? $data['author'] : null;
        $content = (isset($data['content'])) ? $data['content'] : null;
        $category = (isset($data['category'])) ? $data['category'] : null;
        $published = (isset($data['published'])) ? $data['published'] : null;
        $thoughtInfo = (isset($data['info'])) ? $data['info'] : null;

        if (!empty($content) && !empty($author) && !empty($category)) {
            if ($id > 0) {
                $thought = $this->repository->find($id);
            }

            if (!$thought) {
                $thought = new Thought();
            }

            $thought->setTags($tags);
            $thought->setAuthor($author);
            $thought->setContent($content);
            $thought->setCategory($category);
            $thought->setPublished($published);
            $thought->setThoughtInfo($thoughtInfo);

            $this->em->persist($thought);

            return true;
        }

        return false;
    }

    /**
     * @param array $terms
     * @param FinderInterface $finder
     * @return mixed
     */
    private function getNames($terms, $finder) {
        $query = new \Elastica\Query();

        $must = array();

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query->setRawQuery(
            array(
                'filter' => array(
                    'bool' => array(
                        'must' => $must
                    ),
                ),
            )
        );

        $authors = $finder->find($query, 100000);

        $names = [];

        foreach ($authors as $author) {
            $names[] = trim($author->getName());
        }

        return $names;
    }
}
