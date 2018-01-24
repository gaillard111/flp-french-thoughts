<?php

namespace ThoughtBundle\Model;

use Doctrine\ORM\EntityManager;
use Elastica\Query;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use Symfony\Component\DependencyInjection\Container;

/**
 * Class AuthorModel
 * @package ThoughtBundle\Model
 */
class AuthorModel
{
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
     * AuthorModel constructor.
     * @param EntityManager $em
     * @param Container     $container
     */
    public function __construct(EntityManager $em, Container $container)
    {
        $this->em         = $em;
        $this->container  = $container;
        $this->repository = $em->getRepository('ThoughtBundle:Author');
    }

    /**
     * @param $nameStartsWith
     * @return array
     */
    public function getAuthorsByStringStart($nameStartsWith)
    {
        return $this->repository->createQueryBuilder('a')
            ->where('a.name LIKE :name')
            ->setParameter('name', $nameStartsWith . '%')
            ->getQuery()
            ->setMaxResults(50)
            ->getResult();
    }

    /**
     * @param string            $nameStartsWith
     * @param TransformedFinder $finder
     */
    public function getAuthorsByStringStartElastic($nameStartsWith, TransformedFinder $finder)
    {
        $result = $finder->createPaginatorAdapter($this->searchDefault($nameStartsWith));

        return $result;
    }

    /**
     * @param $name
     * @return null|object
     */
    public function findAuthorByName($name) {
        return $this->repository->findOneBy(array(
            'name' => $name
        ));
    }

    /**
     * @param string $nameStartsWith
     * @return Query
     */
    public function searchDefault($nameStartsWith)
    {
        $query = new \Elastica\Query();

        $terms[] = array(
            'query' => array(
                'match_phrase_prefix' => array(
                    'name_prefix' => array(
                        'query' => $nameStartsWith,
                        "max_expansions" => 10000
                    )
                ),
            )
        );

        $must[] = $terms;

        $query = new \Elastica\Query();

        $query->setRawQuery(
            array(
                'filter' => array(
                    'bool' => array(
                        'must' => $must
                    ),
                ),
                'sort' => array(
                    'name_prefix' => 'asc'
                ),
            )
        );

        return $query;
    }


}
