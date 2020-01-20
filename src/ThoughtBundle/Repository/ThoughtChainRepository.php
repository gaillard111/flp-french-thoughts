<?php

namespace ThoughtBundle\Repository;

use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Chain;

/**
 * Class ThoughtChainRepository
 *
 * @package ThoughtBundle\Repository
 */
class ThoughtChainRepository extends EntityRepository
{
    /**
     * @param Chain $chain
     *
     * @return mixed
     *
     * @throws \Doctrine\ORM\NonUniqueResultException
     */
    public function getLastLinkChain(Chain $chain)
    {
        return $this->createQueryBuilder('tc')
            ->where('tc.chain = :chain')
            ->setParameter('chain', $chain)
            ->orderBy('tc.sortIndex', 'desc')
            ->setMaxResults(1)
            ->getQuery()->getOneOrNullResult();
    }

    /**
     * Get sorted ThoughtChain
     *
     * @param Chain $chain
     *
     * @return array
     */
    public function getSortingThoughtChain(Chain $chain)
    {
        return $this->createQueryBuilder('tc')
            ->where('tc.chain = :chain')
            ->setParameter('chain', $chain)
            ->orderBy('tc.sortIndex', 'asc')
            ->getQuery()->getResult();
    }
}
