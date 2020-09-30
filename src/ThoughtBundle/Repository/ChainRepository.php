<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use Doctrine\ORM\Query;

/**
 * Class ChainRepository
 *
 * @package ThoughtBundle\Repository
 */
class ChainRepository extends EntityRepository
{
    public function findChainesByRegex($regex, $roleStudent) {
        $qb = $this->createQueryBuilder('c')
            ->leftJoin('c.user', 'topicowner')
            ->where('REGEXP(c.name, :regexp) = true')
            ->andWhere('c.isPrivate = false')
            ->orderBy('c.name', 'ASC');

            if ($roleStudent) {
                $qb->andWhere('topicowner.roles LIKE :role');
            } else {
                $qb->andWhere('topicowner.roles NOT LIKE :role');
            }

            $qb ->setParameters([
                'regexp' => $regex,
                'role' => '%' . User::ROLE_STUDENT . '%'
            ]);

        return $qb->getQuery()->getResult();
    }

    /**
     * @param $role
     * @return array
     */
    public function getAllSharedChains($role)
    {
        $qb = $this->createQueryBuilder('c');
        $qb
            ->where('c.isPrivate = false')
            ->leftJoin('c.user', 'u');
        if ($role == User::ROLE_STUDENT) {
            $qb->andWhere('u.roles LIKE :roles');
        } else {
            $qb->andWhere('u.roles NOT LIKE :roles');
        }

        $qb->setParameters([
            'roles' => '%' . User::ROLE_STUDENT . '%',
        ]);

        return $qb->getQuery()->getResult();
    }

    /**
     * @return Query
     */
    public function getAllCollectiveChains($role)
    {
        $qb = $this->createQueryBuilder('c');
        $qb
            ->select('c')
            ->where('c.isCollective = true')
            ->leftJoin('c.user', 'u');

        if ($role == User::ROLE_STUDENT) {
            $qb->andWhere('u.roles LIKE :roles');
        } else {
            $qb->andWhere('u.roles NOT LIKE :roles');
        }

        $qb->setParameters([
            'roles' => '%' . User::ROLE_STUDENT . '%',
        ]);
        return $qb->getQuery();
    }

    /**
     * @param $user
     * @return Query
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
