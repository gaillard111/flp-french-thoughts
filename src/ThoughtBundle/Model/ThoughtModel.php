<?php

namespace ThoughtBundle\Model;

use Doctrine\ORM\EntityManager;
use FOS\ElasticaBundle\Finder\TransformedFinder;

/**
 * Class ThoughtModel
 * @package ThoughtBundle\Model
 */
class ThoughtModel
{
    /**
     * @var EntityManager
     */
    protected $em;

    /**
     * @var \Doctrine\ORM\EntityRepository
     */
    protected $repository;

    /**
     * ServiceMedia constructor.
     * @param EntityManager $em
     */
    public function __construct(EntityManager $em)
    {
        $this->em = $em;
        $this->repository = $em->getRepository('ThoughtBundle:Thought');
    }

    /**
     * @return \Doctrine\ORM\Query
     */
    public function getThoughts()
    {
        return $this->repository->createQueryBuilder('t')
            ->orderBy('t.createdAt', 'DESC')
            ->getQuery();
    }

    /**
     * @param array             $request
     * @param TransformedFinder $finder
     * @return array
     */
    public function getThoughtsFromElastic($request, TransformedFinder $finder)
    {
        if (isset($request['words']) and !empty(trim($request['words']))) {
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

            $sort = array();

            if ($request['sorting']) {
                $sort = array(
                    $request['sorting'] => (isset($request['sorting_desc']) ? 'desc' : 'asc'),
                );
            }

            $maxWords = $request['max_words'] == 0 ? 99999999 : intval($request['max_words']);

            $query = new \Elastica\Query\MultiMatch();

            $query->setParams(
                array(
                    'query' => array(
                        'multi_match' => array(
                            'query' => $request['words'],
                            'fields' => $fields,
                        ),
                    ),
                    'filter' => array(
                        'range' => array(
                            'amount' => array(
                                'gte' => intval($request['min_words']),
                                'lte' => $maxWords,
                            ),
                        ),
                    ),
                    'sort' => $sort,
                )
            );

            $thoughts = $finder->find($query);

            return $thoughts;
        } else {
            return $this->getThoughts();
        }
    }
}
