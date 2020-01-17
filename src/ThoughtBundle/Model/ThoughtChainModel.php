<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\OptimisticLockException;
use Elastica\Query;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtChainModel
 * @package ThoughtBundle\Model
 */
class ThoughtChainModel
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
     * @var mixed
     */
    protected $user;

    /**
     * ThoughtModel constructor.
     * @param EntityManager $em
     * @param Container $container
     * @throws \Exception
     */
    public function __construct(EntityManager $em, Container $container)
    {
        $this->em        = $em;
        $this->container = $container;
        $this->user      = $container->get('security.token_storage')->getToken()->getUser();
    }

    /**
     * Sorting ThoughtCains
     *
     * @param Chain $chain
     * @throws OptimisticLockException
     */
    public function thoughtChainSort(Chain $chain)
    {
        $thoughtChains = $this->em->getRepository('ThoughtBundle:ThoughtChain')->getSortingThoughtChain($chain);

        $index = 1;

        foreach ($thoughtChains as $thoughtChain) {
            $thoughtChain->setSortIndex($index);
            $this->em->persist($thoughtChain);

            $index++;
        }

        $this->em->flush();
    }
}
