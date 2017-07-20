<?php

namespace ThoughtBundle\Model;

use Doctrine\ORM\EntityManager;
use Elastica\Query;
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
     * @param $name
     * @return null|object
     */
    public function findAuthorByName($name) {
        return $this->repository->findOneBy(array(
            'name' => $name
        ));
    }


}
