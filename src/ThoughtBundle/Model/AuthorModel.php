<?php

namespace ThoughtBundle\Model;

use Doctrine\ORM\EntityManager;
use Doctrine\ORM\EntityRepository;
use Elastica\Query;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface;
use FOS\ElasticaBundle\Paginator\TransformedPaginatorAdapter;
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
     * @var EntityRepository
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
     * @param string $nameStartsWith
     * @param TransformedFinder $finder
     * @return PaginatorAdapterInterface|TransformedPaginatorAdapter
     */
    public function getAuthorsByStringStartElastic($nameStartsWith, TransformedFinder $finder)
    {
        return $finder->createPaginatorAdapter($this->searchDefault($nameStartsWith));
    }

    /**
     * @param $name
     * @return null|object
     */
    public function findAuthorByName($name) {
        return $this->repository->findOneBy([
            'name' => $name
        ]);
    }

    /**
     * @param string $nameStartsWith
     * @return Query
     */
    public function searchDefault($nameStartsWith)
    {
        $query = new Query();

        $terms[] = [
            'query' => [
                'match_phrase_prefix' => [
                    'name_prefix' => [
                        'query' => $nameStartsWith,
                        "max_expansions" => 10000
                    ]
                ],
            ]
        ];

        $must[] = $terms;

        $query = new Query();

        $query->setRawQuery(
            [
                'filter' => [
                    'bool' => [
                        'must' => $must
                    ],
                ],
                'sort' => [
                    'name_prefix' => 'asc'
                ],
            ]
        );

        return $query;
    }


}
