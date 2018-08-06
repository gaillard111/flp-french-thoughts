<?php

namespace ThoughtBundle\Repository;

use Doctrine\ORM\EntityRepository;

/**
 * Class ChainRepository
 * @package ThoughtBundle\Repository
 */
class ChainRepository extends EntityRepository
{
    /**
     * Get all shared chains
     *
     * @return array
     */
    public function getAllSharedChains()
    {
        return $this->createQueryBuilder('c')
            ->where('c.isPrivate = false')
            ->getQuery()->getResult();
    }

    /**
     * @param $user
     * @return \Doctrine\ORM\Query
     */
    public function getAllFavoriteChains($user)
    {
        return $this->createQueryBuilder('c')
            ->andWhere('c.favorite = true')
            ->andWhere('c.user = :user')
            ->setParameter('user', $user)
            ->getQuery();
    }
}
