<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\EntityRepository;
use Doctrine\ORM\OptimisticLockException;
use Doctrine\ORM\Query as DoctrineQuery;
use Doctrine\ORM\Query\QueryException;
use Elastica\Query;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use FOS\ElasticaBundle\Paginator\TransformedPaginatorAdapter;
use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtModel
 *
 * @package ThoughtBundle\Model
 */
class ThoughtModel
{
    const CLOUD_MIN_FONT_SIZE = 15;

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
     * @var EntityRepository
     */
    protected $repository;

    /**
     * @var TransformedFinder
     */
    private $finder;

    /**
     * @var TransformedFinder
     */
    private $authorsFinder;

    /**
     * ThoughtModel constructor.
     *
     * @param EntityManager $em
     * @param Container     $container
     */
    public function __construct(EntityManager $em, Container $container, TransformedFinder $finder, TransformedFinder $authorsFinder)
    {
        $this->em         = $em;
        $this->container  = $container;
        $this->repository = $em->getRepository('ThoughtBundle:Thought');

        $this->finder        = $finder;
        $this->authorsFinder = $authorsFinder;
    }

    /**
     * @param User $user
     *
     * @return DoctrineQuery
     */
    public function getUserThoughts(User $user, $order = 'DESC', $searchString = '')
    {
        $qb = $this->repository->createQueryBuilder('t');

        if ($searchString) {
            $words = explode(' ', $searchString);

            foreach ($words as $id => $word) {
                $qb
                    ->andWhere('t.content LIKE :word' . $id)
                    ->setParameter('word' . $id, '%' . $word . '%');
            }
        }

        $qb
            ->andWhere('t.owner = :user')
            ->orderBy('t.createdAt', $order)
            ->setParameter('user', $user);

        return $qb->getQuery();
    }

    /**
     * @param User $user
     *
     * @return mixed
     *
     * @throws QueryException
     */
    public function getCountUserThoughts(User $user)
    {
        return $this->repository->createQueryBuilder('t')
            ->select('count(t.owner)')
            ->andWhere('t.owner = :user')
            ->setParameter('user', $user)
            ->getQuery()
            ->getSingleScalarResult();
    }

    /**
     * @param $search
     * @param $default
     * @param int $page
     *
     * @return PaginatorAdapterInterface|Thought[]
     */
    public function getThoughts($search, $default, $page = 1)
    {
        if ($search || $default) {
            /** @var PaginatorAdapterInterface $thoughts */
            $thoughts = $this->getThoughtsFromElastic($search, $page);
        } else {
            $thoughts = $this->getLastThoughts(50 * $page, 'amount');
        }

        return $thoughts;
    }

    /**
     * @param array $request
     *
     * @return DoctrineQuery|PaginatorAdapterInterface|TransformedPaginatorAdapter
     */
    public function getThoughtsFromElastic($request, $page)
    {
        $fields = [
            'tags',
            'author',
            'content',
            'category',
            'thoughtInfo',
        ];

        if (isset($request['field']) && count($request['field']) > 0) {
            $fields = array_keys($request['field']);
        }

        $isAuthor = false;

        $terms = [];

        if (isset($request['author']) && count($request['author']) > 0) {
            $authorsData = $this->getAuthors($request['author'], $isAuthor);

            $terms = array_merge($terms, $authorsData['terms']);

            $isAuthor = $authorsData['isAuthor'];
        }

        $names = [];

        if ($isAuthor) {
            $names = $this->getNames($terms);

            $terms[] = [
                'terms' => [
                    'author_exact' => $names,
                ],
            ];
        }

        if (isset($request['term']) && count($request['term']) > 0) {
            $terms = array_merge($terms, $this->getTerms($request['term']));
        }

        $sort = ['createdAt' => 'desc'];

        if (isset($request['sorting']) && $request['sorting']) {
            if (isset($request['sorting_desc'])) {
                if ($request['sorting_desc'] == 'true') {
                    $sortingDirection = 'desc';
                } else {
                    $sortingDirection = 'asc';
                }

                $sort = [
                    $request['sorting'] => $sortingDirection,
                ];
            }
        }

        $strict = isset($request['strict']) && $request['strict'];

        $maxWords = (isset($request['max_words']) && $request['max_words'] > 0) ? intval($request['max_words']) : 99999999;

        $minWords = isset($request['min_words']) ? intval($request['min_words']) : 0;

        $words = (isset($request['words']) && mb_strlen($request['words']) > 0) ? trim($request['words']) : null;

        $lastChar  = $words[mb_strlen($words) - 1];
        $firstChar = $words[0];

        $words = ($lastChar == ',' || $lastChar == '.' || $lastChar == '!') ? mb_substr($words, 0, -1) : $words;
        $words = ($firstChar == ',' || $firstChar == '.' || $firstChar == '!') ? mb_substr($words, 1) : $words;

        $countQuote = explode('"', $words);

        if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
            $query = $this->searchQuoteString($countQuote[1], $fields, $minWords, $maxWords, $sort, $terms);

            return $this->finder->createPaginatorAdapter($query);
        }

        $arrWords = explode(' ', $words);

        $wordExceptions = [];

        foreach ($arrWords as $keyArrWords => $valueArrWords) {
            if (empty($valueArrWords)) {
                continue;
            }
            if ($valueArrWords[0] == '-') {
                $wordExceptions[] = $this->filterWord($valueArrWords);
                unset($arrWords[$keyArrWords]);
            }
        }

        $words = implode(' ', $arrWords);

        $filterException = $this->compileExceptions($fields, $wordExceptions);

        if (!$words) {
            return $this->getLastThoughts(50 * $page, array_keys($sort)[0], $sort[array_keys($sort)[0]]);
        }

        if ($strict) {
            $query = $this->searchExactly($words, $fields, $minWords, $maxWords, $sort);
            return $this->finder->createPaginatorAdapter($query);
        }

        $words = $this->filterWord($words);

        if (count(explode(' ', $words)) > 1) {
            if ($request['sorting'] == '') {
                $sort = ['amount' => 'asc'];
            }
            $query = $this->searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms);
            return $this->finder->createPaginatorAdapter($query);
        }

        $query = $this->searchWord($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms);

        return $this->finder->createPaginatorAdapter($query);
    }

    /**
     * @param array $data
     *
     * @return int
     *
     * @throws OptimisticLockException
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
     *
     * @return Thought
     *
     * @throws OptimisticLockException
     */
    public function addLike(Thought $thought, User $user)
    {
        $like = new Like();
        $like
            ->setUser($user)
            ->setThought($thought);
        $thought->addLike($like);
        $this->em->persist($thought);
        $this->em->flush();
        return $thought;
    }

    /**
     * @param Thought $thought
     *
     * @return Thought
     *
     * @throws OptimisticLockException
     */
    public function removeLike(Thought $thought, User $user)
    {
        /** @var Like[] $likes */
        $likes = $thought->getLikes();

        foreach ($likes as $like) {
            if ($like->getUser() === $user) {
                $this->em->remove($like);
                $this->em->flush();
            }
        }

        return $thought;
    }

    /**
     * @param array $filters
     * @param array $filterFields
     *
     * @return array
     */
    public function getFilteredThoughts(array $filters, array $filterFields)
    {
        $where     = [];
        $sortBy    = null;
        $sortOrder = null;

        if (count($filters)) {
            $sortBy    = isset($filters['_sort_by']) ? $filters['_sort_by'] : null;
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
     *
     * @return Query
     */
    public function searchExactly($words, $fields, $minWords, $maxWords, $sort)
    {
        $query = new Query();

        $arrFields = [];

        foreach ($fields as $field) {
            $arrFields[] = [
                'bool' => [
                    'must' => [
                        'term' => [
                            ($field . '_exact') => $words,
                        ],
                    ],
                ],
            ];
        }

        $arr = [
            'filter' => [
                'bool' => [
                    'should' => $arrFields,
                    'must'   => [
                        'range' => [
                            'amount' => [
                                'gte' => $minWords,
                                'lte' => $maxWords,
                            ],
                        ],
                    ],
                ],
            ],
            'sort' => $sort,
        ];

        return $query->setParams($arr);
    }

    /**
     * @param $words
     * @param $fields
     * @param $minWords
     * @param $maxWords
     * @param $sort
     * @param $filterException
     * @param $terms
     *
     * @return Query
     */
    public function searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms)
    {
        $query = new Query();

        $must = [
            [
                'range' => [
                    'amount' => [
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ],
                ],
            ],
        ];

        if (!empty($terms)) {
            $must[] = $terms;
        }

        return $query->setParams(
            [
                'query' => [
                    'multi_match' => [
                        'query'                => $words,
                        'fields'               => $fields,
                        'minimum_should_match' => '100%',
                        'type'                 => 'cross_fields',
                        'operator'             => 'and',
                        'tie_breaker'          => '1.0',
                        'analyzer'             => 'standard',
                    ],
                ],
                'filter' => [
                    'bool' => [
                        'must_not' => $filterException,
                        'must'     => $must,
                    ],
                ],
                'sort' => $sort,
            ]
        );
    }

    /**
     * @param string $words
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     * @param array  $filterException
     *
     * @return Query
     */
    public function searchWord($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms)
    {
        $must = [
            [
                'range' => [
                    'amount' => [
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ],
                ],
            ],
        ];

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query = new Query();
        $query->setParams(
            [
                'query' => [
                    'multi_match' => [
                        'query'                => $words,
                        'fields'               => $fields,
                        'operator'             => 'and',
                        'minimum_should_match' => '100%',
                    ],
                ],
                'filter' => [
                    'bool' => [
                        'must_not' => $filterException,
                        'must'     => $must,
                    ],
                ],
                'sort' => $sort,
            ]
        );

        return $query;
    }

    /**
     * @param int   $minWords
     * @param int   $maxWords
     * @param array $sort
     * @param array $filterException
     *
     * @return Query
     */
    public function searchDefault($minWords, $maxWords, $sort, $filterException, $terms)
    {
        $must = [
            [
                'range' => [
                    'amount' => [
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ],
                ],
            ],
        ];

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query = new Query();

        $query->setRawQuery(
            [
                'filter' => [
                    'bool' => [
                        'must_not' => $filterException,
                        'must'     => $must,
                    ],
                ],
                'sort' => $sort,
            ]
        );

        return $query;
    }

    /**
     * @param string $string
     * @param array  $fields
     * @param int    $minWords
     * @param int    $maxWords
     * @param array  $sort
     *
     * @return $this|Query
     */
    public function searchQuoteString($string, $fields, $minWords, $maxWords, $sort, $terms)
    {
        $query = new Query();

        $must = [
            [
                'range' => [
                    'amount' => [
                        'gte' => $minWords,
                        'lte' => $maxWords,
                    ],
                ],
            ],
        ];

        if (!empty($terms)) {
            $must[] = $terms;
        }

        if (count(explode(' ', $string)) > 1) {
            $phraseFields = [];

            foreach ($fields as $field) {
                $phraseFields[] = $field . '_phrase';
            }

            $query->setParams([
                'query' => [
                    'multi_match' => [
                        'query'                => $string,
                        'fields'               => $phraseFields,
                        'operator'             => 'and',
                        'minimum_should_match' => '100%',
                        'type'                 => 'phrase',
                    ],
                ],
                'filter' => [
                    'bool' => [
                        'must' => $must,
                    ],
                ],
                'sort' => $sort,
            ]);

            return $query;
        }

        $arrFields = [];

        foreach ($fields as $field) {
            $arrFields[] = [
                'prefix' => [
                    ($field . '_phrase') => $string,
                ],
            ];
        }

        $arr = [
            'filter' => [
                'bool' => [
                    'should' => $arrFields,
                    'must'   => $must,
                ],
            ],
            'sort' => $sort,
        ];

        return $query->setParams($arr);
    }

    /**
     * @param $limit
     *
     * @return mixed
     */
    public function getLastThoughts($limit, $sortField, $sortDirection = 'ASC')
    {
        return $this->repository->getLastThoughts($limit, $sortField, $sortDirection);
    }

    /**
     * @param array                     $fields
     * @param PaginatorAdapterInterface $thoughts
     *
     * @return array
     */
    public function getCloud($fields, $thoughts, $words)
    {
        $cloud = $cloudStyle = [];

        $avoidWords = [
            'alors', 'aussi', 'celui', 'celle', 'cette',
            'contre', 'comme', 'depuis', 'elles', 'leurs',
            'même', 'moins', 'notre', 'quand', 'votre', 'toute',
            'avait', 'avaient', 'autre', 'beaucoup', 'chose', 'choses',
            'entre', 'encore', 'était', 'étaient', 'lequel', 'parce',
            'parle', 'parlent', 'quelque', 'sommes', 'seule', 'toutes',
        ];

        if (!is_array($thoughts) && $words) {
            $cloud        = [];
            $cloudContent = [];

            if ($thoughts->getTotalHits() > 0) {
                /** @var Thought $thought */
                if ($thoughts->getTotalHits() > 5000) {
                    $offset = 5000;
                } else {
                    $offset = $thoughts->getTotalHits();
                }
                foreach ($thoughts->getResults(0, $offset)->toArray() as $thought) {
                    $tags  = explode(',', $thought->getTags());
                    $words = explode(' ', $thought->getContent());
                    if (count($words) <= 80) {
                        foreach ($words as $word) {
                            if (in_array($this->formatCloudWord($word), $avoidWords)) {
                                continue;
                            }

                            if (mb_strlen($this->formatCloudWord($word), 'UTF-8') >= 5) {
                                if (!isset($cloudContent[$this->formatCloudWord($word)])) {
                                    $cloudContent[$this->formatCloudWord($word)] = 0;
                                }

                                $cloudContent[$this->formatCloudWord($word)]++;
                            }
                        }
                    }

                    foreach ($tags as $tag) {
                        if (!$tag || mb_strlen($this->formatCloudWord($tag), 'UTF-8') < 5 || in_array($this->formatCloudWord($tag), $avoidWords)) {
                            continue;
                        }

                        if (!isset($cloud[$this->formatCloudWord($tag)])) {
                            $cloud[$this->formatCloudWord($tag)] = 0;
                        }

                        $cloud[$this->formatCloudWord($tag)]++;
                    }

                    if (!$thought->getCategory()) {
                        continue;
                    }
                }
            }

            array_multisort($cloud, SORT_DESC);
            array_multisort($cloudContent, SORT_DESC);

            $cloud        = array_slice($cloud, 0, self::CLOUD_NUMBER_OF_WORDS / 2);
            $cloudContent = array_slice($cloudContent, 0, self::CLOUD_NUMBER_OF_WORDS / 2);

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
            'cloudStyle' => $cloudStyle,
        ];
    }

    /**
     * @param $requestAuthor array
     *
     * @return array
     */
    private function getAuthors($requestAuthor, $isAuthor)
    {
        $terms = [];

        foreach ($requestAuthor as $key => $val) {
            if ($val) {
                $isAuthor = true;

                $val = trim($val);

                $countQuote = explode('"', $val);

                if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
                    $val = $countQuote[1];

                    $terms[] = [
                        'query' => [
                            'term' => [
                                $key . '_exact' => $val,
                            ],
                        ],
                    ];
                } else {
                    $terms[] = [
                        'query' => [
                            'multi_match' => [
                                'query'  => $val,
                                'fields' => [
                                    $key,
                                ],
                                'minimum_should_match' => '100%',
                                'type'                 => 'cross_fields',
                                'operator'             => 'and',
                                'tie_breaker'          => '1.0',
                                'analyzer'             => 'standard',
                            ],
                        ],
                    ];
                }
            }
        }

        return [
            'terms'    => $terms,
            'isAuthor' => $isAuthor,
        ];
    }

    /**
     * @param $requestTerms array
     *
     * @return array
     */
    private function getTerms($requestTerms)
    {
        $terms = [];

        foreach ($requestTerms as $key => $val) {
            if ($val) {
                $val = trim($val);

                $countQuote = explode('"', $val);

                if (count($countQuote) == 3 && empty($countQuote[0]) && empty($countQuote[2])) {
                    $terms[] = [
                        'query' => [
                            'match_phrase' => [
                                $key . '_phrase' => $val,
                            ],
                        ],
                    ];
                } else {
                    $terms[] = [
                        'query' => [
                            'match' => [
                                $key . '_phrase' => $val,
                            ],
                        ],
                    ];
                }
            }
        }

        return $terms;
    }

    /**
     * return value of font-size depends on popularity
     *
     * @param $val
     *
     * @return int
     */
    private function cloudFontSize($val)
    {
        return self::CLOUD_MIN_FONT_SIZE + sqrt($val);
    }

    /**
     * return value of font-weight depends on popularity
     *
     * @param $val
     *
     * @return int
     */
    private function cloudFontWeight($val)
    {
        $weight = ceil((self::CLOUD_MIN_FONT_WEIGHT * sqrt($val) / 100)) * 100;

        return $weight > 900 ? 900 : $weight;
    }

    /**
     * @param string $word
     *
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
     *
     * @return array
     */
    private function compileExceptions($fields, $words)
    {
        $result = [];

        if (count($words)) {
            foreach ($fields as $field) {
                $arrWords = [];

                foreach ($words as $word) {
                    $arrWords[] = [
                        'term' => [
                            $field => $word,
                        ],
                    ];
                }

                $result[] = $arrWords;
            }
        }

        return $result;
    }

    /**
     * @param array $data
     *
     * @return bool|int
     */
    private function createTransaction(array $data)
    {
        $thought = null;

        $id          = (isset($data['id'])) ? $data['id'] : null;
        $tags        = (isset($data['tags'])) ? $data['tags'] : null;
        $author      = (isset($data['author'])) ? $data['author'] : null;
        $content     = (isset($data['content'])) ? $data['content'] : null;
        $category    = (isset($data['category'])) ? $data['category'] : null;
        $published   = (isset($data['published'])) ? $data['published'] : null;
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

    private function formatCloudWord($word)
    {
        $trimChars = "\:\"\'\.\,\; \t\n\r\0\x0B";

        $word = trim(strtolower($word), $trimChars);

        if (strpos($word, "'") !== false) {
            return '';
        }

        return $word;
    }

    /**
     * @param $terms
     *
     * @return array
     */
    private function getNames($terms)
    {
        $query = new Query();

        $must = [];

        if (!empty($terms)) {
            $must[] = $terms;
        }

        $query->setRawQuery([
            'filter' => [
                'bool' => [
                    'must' => array_merge($must, [
                        [
                            'regexp' => [
                                'birthDate' => [
                                    'value' => '6.*5',
                                ],
                            ],
                        ],
                    ]),
                ],
            ],
        ]);
        $authors = $this->authorsFinder->find($query, 100000);

        $names = [];

        foreach ($authors as $author) {
            $names[] = trim($author->getName());
        }

        return $names;
    }
}
