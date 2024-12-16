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
    use LikeModelTrait;

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
    public function getThoughts($search, $role, $page = 1)
    {
        if ($search) {
            /** @var PaginatorAdapterInterface $thoughts */
            $thoughts = $this->getThoughtsFromElastic($search, $page, $role);
        } else {
            $thoughts = $this->getLastThoughts(50 * $page, 'id', $role, 'DESC');
        }

        return $thoughts;
    }

    /**
     * @param array $request
     * @return DoctrineQuery|PaginatorAdapterInterface|TransformedPaginatorAdapter
     */
    public function getThoughtsFromElastic($request, $page, $role)
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

        $ngram = isset($request['field']['ngram']) && $request['field']['ngram'];
        $ngramFields = [];

        foreach ($fields as $field) {
            $fields[] = $field . '_dop';
            if ($ngram) {
                $ngramFields[] = $field . '_ngram';
            }
        }

        $authors = [];
        if (isset($request['author']) && in_array(!null, $request['author'])) {

            $names = $this->getNames($request['author']);

            if (!$names) {
                return [];
            }

            foreach ($names as $key => $name) {
                $authors[] = [
                    'term' => [
                        'author_exact' => $name,
                    ],
                ];
            }
        }

        $terms = [];
        if (isset($request['term']) && in_array(!null, $request['term'])) {
            $terms = $this->getTerms($request['term']);
        }

        $sort = ['amount' => 'asc'];
        if (isset($request['sorting']) && $request['sorting'] !== "") {

            $sortingDirection = 'asc';

            if (isset($request['sorting_desc'])) {
                if ($request['sorting_desc'] == 'on') {
                    $sortingDirection = 'desc';
                }
            }

            $sort = [
                $request['sorting'] => $sortingDirection,
            ];
        }

        $strict = isset($request['field']['strict']) && $request['field']['strict'];

        $maxWords = (isset($request['max_words']) && $request['max_words'] > 0) ? intval($request['max_words']) : 10000;

        $minWords = isset($request['min_words']) ? intval($request['min_words']) : 0;

        $words = (isset($request['words']) && mb_strlen($request['words']) > 0) ? trim($request['words']) : null;

        $arrWords = explode(' ', $words);

        $complex = false;

        $haveLink = false;

        if ($words) {
            foreach ($arrWords as $word) {
                $signs = ['"', '-', '+',];
                if (in_array($word[0], $signs) || in_array(mb_substr($word, -1), $signs)) {
                    $complex = true;
                    break;
                }
            }
        }

        if (strpos($words, '[a]') !== false) {
            $haveLink = true;
        }

        if ($words && ($complex || $haveLink)) {
            $lastChar  = $words[mb_strlen($words) - 1];
            $firstChar = $words[0];

            $words = ($lastChar == ',' || $lastChar == '.' || $lastChar == '!') ? mb_substr($words, 0, -1) : $words;
            $words = ($firstChar == ',' || $firstChar == '.' || $firstChar == '!') ? mb_substr($words, 1) : $words;

            $query = $this->complexSearch($words, $fields, $minWords, $maxWords, $sort, $terms, $authors, $ngram, $haveLink);

            return $this->finder->createPaginatorAdapter($query);
        }

        $filterException = [];

        if (!$words) {
            $query = $this->searchDefault($minWords, $maxWords, $sort, $filterException, $terms, $authors);
            return $this->finder->createPaginatorAdapter($query);
        }

        if ($strict) {
            $query = $this->searchExactly($words, $fields, $minWords, $maxWords, $sort);
            return $this->finder->createPaginatorAdapter($query);
        }

        if (count(explode(' ', $words)) > 1) {
            if ($request['sorting'] == '') {
                $sort = ['amount' => 'asc'];
            }
        }

        $fields = array_merge($fields, $ngramFields);

        $query = $this->searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms, $role, $authors);

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
    public function searchFullText($words, $fields, $minWords, $maxWords, $sort, $filterException, $terms, $role, $authors)
    {
        $boolSearchArray = $filterException;

        if ($role == User::ROLE_USER) {
            $boolSearchArray[] = [
                'term' => [
                    'ownerStudent' => true,
                ],
            ];
        }

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

        $words = mb_strtolower($words, 'UTF-8');

        $query = new Query();
        $query->setParams([
            'query' => [
                'filtered' => [
                    'query' => [
                        'multi_match' => [
                            'query'                => $words,
                            'fields'               => $fields,
                            'minimum_should_match' => '100%',
                            'type'                 => 'cross_fields',
                            'operator'             => 'and',
                            'tie_breaker'          => '1.0',
                            'analyzer'             => 'whitespace',
                        ],
                    ],
                    'filter' => [
                        'bool' => [
                            'must_not' => $boolSearchArray,
                            'should'     => $authors,
                            'must'     => $must,
                        ],
                    ],
                ],
            ],
            'sort' => $sort,
        ]);

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
    public function searchDefault($minWords, $maxWords, $sort, $filterException, $terms, $authors)
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
                        'should'     => $authors,
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
     * @return Query
     */
    public function complexSearch($string, $fields, $minWords, $maxWords, $sort, $terms, $authors, $ngram, $haveLink)
    {
        $query = new Query();

        $mustFilter = [
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
            $mustFilter[] = $terms;
        }

        $phraseFields = [];
        $ngramFields = [];

        foreach ($fields as $field) {
            $phraseFields[] = $field . '_phrase^3';
            if ($ngram) {
                $ngramFields[] = $field . '_ngram^0.5';
            }
        }
        $string = mb_strtolower($string);

        if ($haveLink) {
            preg_match_all('/\[a[^\]]*\](.*?)\[\/a\]/', $string, $matches);

            $linkPatterns = [];
            foreach ($matches[1] as $match) {
                if ($ngram) {
                    $linkPatterns[] = '\\[a [^\\]]*\\]([^\\[]*' . $match . '[^\\[]*)\\[/a\\]';
                } else {
                    $linkPatterns[] = '\\[a [^\\]]*([^\\[]*[ \\]]' . $match .'[^\\[]*)\\[/a\\]';
                }
            }

            $linkRegexpStr = '.*(' . implode('|', $linkPatterns) . ').*';

            $string = trim(preg_replace('/\[a[^\]]*\](.*?)\[\/a\]/', '', $string));
        }

        $must = [];
        $mustNot = [];

        $stringQuotes = '';
        $stringSpace = '';
        $stringMinus = '';

        if (preg_match_all('/"([^"]+)"/', $string, $m)) {
            $stringQuotes = implode(' ', $m[0]);
        }
        foreach ($m[0] as $str) {
            $string = str_replace($str, '', $string);
        }
        $string = trim($string);

        foreach(explode(' ', $string) as $word) {
            if (!isset($word[0])) {
                continue;
            }

            if ($word[0] == '-') {
                $stringMinus .= substr($word, 1) . ' ';
            } else if ($word[0] == '+') {
                $stringQuotes .= ' ' . $word;
            } else {
                $stringSpace .= $word . ' ';
            }
        }

        if ($stringQuotes) {
            $must[] = [
                'simple_query_string' => [
                    'query' => $stringQuotes,
                    'fields' => $phraseFields,
                    'default_operator' => 'and',
                ],
            ];
        }

        if ($stringSpace) {
            $must[] = [
                'multi_match' => [
                    'query' => $stringSpace,
                    'fields' => $ngram ? $ngramFields : $fields,
                    'type' => 'cross_fields',
                    'operator' => 'and',
                    'analyzer' => 'whitespace',
                ],
            ];
        }

        $mustNot = [
            [
                'multi_match' => [
                    'query' => $stringMinus,
                    'fields' => $ngram ? $ngramFields : $fields,
                    'type' => 'cross_fields',
                    'operator' => 'and',
                    'analyzer' => 'whitespace',
                ],
            ],
        ];

        if ($haveLink) {
            $must[] = [
                'regexp' => [
                    'content_sort' => $linkRegexpStr,
                ]
            ];
        }

        $query->setParams([
            'query' => [
                'bool' => [
                    'must' => $must,
                    'must_not' => $mustNot,
                ],
            ],
            'filter' => [
                'bool' => [
                    'must' => $mustFilter,
                    'should' => $authors
                ],
            ],
            'sort' => $sort,
        ]);

        return $query;
    }

    /**
     * @param $limit
     *
     * @return mixed
     */
    public function getLastThoughts($limit, $sortField, $role, $sortDirection = 'DESC')
    {
        return $this->repository->getLastThoughts($limit, $sortField, $sortDirection, $role);
    }

    /**
     * @param array $fields
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
            'ainsi', 'appelons', 'autres', 'chacun', 'chaque', 'celles', 'celles-ci',
            'certains', 'c’est', 'court', 'cours', 'devrions', 'd\'une, n’est',
            'place', 'point', 'plutôt', 'pourrez', 'peuvent', 'propre', 'propres', 'peut-être',
            'quelle', 'quelques', 'qu’elle', 'qu’il', 's’est', 'selon', 'seulement', 'seules', 'serez',
            'semble', 'souvent', 'tellement', 'vient', 'vraiment', '&lt',  '&gt', 'qu’on', 'n\'est'
        ];

        if (!is_array($thoughts) && method_exists($thoughts, 'getTotalHits') && $words) {
            $cloud        = [];
            $cloudContent = [];

            if ($thoughts->getTotalHits() > 0) {
                /** @var Thought $thought */
                $offset = $thoughts->getTotalHits();
                if ($offset > 100) {
                    $offset = 100;
                }
                foreach ($thoughts->getResults(0, $offset)->toArray() as $thought) {

                    $tags  = explode(',', $thought->getTags());
                    $words = explode(' ', strip_tags(htmlspecialchars_decode($thought->getContent())));

                    foreach ($words as $key => $word) {
                        if (in_array($this->formatCloudWord($word), $avoidWords)) {
                            continue;
                        }

                        if (mb_strlen($this->formatCloudWord($word), 'UTF-8') >= 5) {
                            if (!isset($cloudContent[$this->formatCloudWord($word)])) {
                                $cloudContent[$this->formatCloudWord($word)] = 0;
                            }

                            $cloudContent[$this->formatCloudWord($word)]++;
                        }

                        if ($key >= 80) {
                            break;
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
                                $key . '_phrase' => preg_replace('/\-/', ' ', $val),
                            ],
                        ],
                    ];
                } else {
                    $terms[] = [
                        'query' => [
                            'match' => [
                                $key . '_phrase' => preg_replace('/\-/', ' ', $val),
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
                    $result[] = [
                        'term' => [
                            $field => $word,
                        ],
                    ];
                }
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
    private function getNames($request)
    {
        $terms['name']      = [];
        $terms['birthDate'] = [];
        $terms['sex']       = [];
        $terms['country']   = [];
        $terms['continent'] = [];
        $terms['job']       = [];

        if (!empty($request['name'])) {
            $name      = explode(' ', trim($request['name']));
            $firstname = array_shift($name);
            $firstname = mb_strtolower($firstname, 'UTF-8');
            $terms['name'] = [
                'regexp' => [
                    'name' => [
                        'value' => $firstname,
                    ],
                ],
            ];
        }
        if (!empty($request['birthDate'])) {
            $birthDate = str_replace('?', '.', $request['birthDate']);
            if (isset($request['av1000']) && ($request['av1000'] == 'on')) {
                $birthDate = '[^1]' . $birthDate;
            }
        }

        if (isset($request['avjc'])) {
            if (isset($request['avjc']) && ($request['avjc'] == 'on')) {
                $birthDate = 'j|c';
            }
        }

        if (isset($birthDate)) {
            $terms['birthDate'] = [
                'regexp' => [
                    'birthDate' => [
                        'value' => $birthDate . '.*|.*' . $birthDate,
                    ],
                ],
            ];
        }
        if (!empty($request['sex'])) {
            $terms['sex'] = [
                'match' => [
                    'sex' => [
                        'query' => $request['sex'],
                    ],
                ],
            ];
        }

        if (!empty($request['country'])) {
            $terms['country'] = [
                'regexp' => [
                    'country' => [
                        'value' => mb_strtolower($request['country'], 'UTF-8') . '.*|.*' . mb_strtolower($request['country'], 'UTF-8'),
                    ],
                ],
            ];
        }

        if (!empty($request['continent'])) {
            $terms['continent'] = [
                'regexp' => [
                    'continent' => [
                        'value' => mb_strtolower($request['continent'], 'UTF-8') . '.*|.*' . mb_strtolower($request['continent'], 'UTF-8') . '|'
                        .ucfirst(mb_strtolower($request['continent'], 'UTF-8')) . '.*|.*' . ucfirst(mb_strtolower($request['continent'], 'UTF-8')),
                    ],
                ],
            ];
        }

        if (!empty($request['job'])) {
            $terms['job'] = [
                'regexp' => [
                    'job' => [
                        'value' => mb_strtolower($request['job'], 'UTF-8'),
                    ],
                ],
            ];
        }

        $query = new Query();

        $must = [];

        if (!empty($terms['sex'])) {
            $must = array_merge($must, [$terms['sex']]);
        }

        if (!empty($terms['birthDate'])) {
            $must = array_merge($must, [$terms['birthDate']]);
        }

        if (!empty($terms['name'])) {
            $must = array_merge($must, [$terms['name']]);
        }

        if (!empty($terms['continent'])) {
            $must = array_merge($must, [$terms['continent']]);
        }

        if (!empty($terms['country'])) {
            $must = array_merge($must, [$terms['country']]);
        }

        if (!empty($terms['job'])) {
            $must = array_merge($must, [$terms['job']]);
        }

        $filter = [
            'query' => [
                'bool' => [
                    'must' => $must,
                ],
            ],
        ];

        $query->setRawQuery([
            'query' => [
                'filtered' => $filter,
            ],
        ]);

        $authors = $this->authorsFinder->find($query, 10000);

        $names = [];

        foreach ($authors as $author) {
            $names[] = trim($author->getName());
        }

        return $names;
    }
}
