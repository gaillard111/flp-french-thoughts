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
    public function findChainesByRegex($regex, $role) {
        $qb = $this->createQueryBuilder('c')
            ->leftJoin('c.user', 'topicowner')
            ->where('REGEXP(c.name, :regexp) = true')
            ->andWhere('c.isPrivate = false')
            ->orderBy('c.name', 'ASC');

            if ($role == User::ROLE_STUDENT || $role == User::ROLE_TEACHER) {
                $qb->andWhere('topicowner.roles LIKE :role1 OR topicowner.roles LIKE :role2');
            } else {
                $qb->andWhere('topicowner.roles NOT LIKE :role1 AND topicowner.roles NOT LIKE :role2');
            }

            $qb ->setParameters([
                'regexp' => $regex,
                'role1' => '%'. User::ROLE_STUDENT. '%',
                'role2' => '%'. User::ROLE_TEACHER. '%'
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
        if ($role == User::ROLE_STUDENT || $role == User::ROLE_TEACHER) {
            $qb->andWhere('u.roles LIKE :role1 OR u.roles LIKE :role2');
        } else {
            $qb->andWhere('u.roles not LIKE :role1 AND u.roles not LIKE :role2');
        }

        $qb->setParameters([
            'role1' => '%'. User::ROLE_STUDENT. '%',
            'role2' => '%'. User::ROLE_TEACHER. '%'
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

        if ($role == User::ROLE_STUDENT || $role == User::ROLE_TEACHER) {
            $qb->andWhere('u.roles LIKE :role1 OR u.roles LIKE :role2');
        } else {
            $qb->andWhere('u.roles not LIKE :role1 AND u.roles not LIKE :role2');
        }

        $qb->setParameters([
            'role1' => '%'. User::ROLE_STUDENT. '%',
            'role2' => '%'. User::ROLE_TEACHER. '%'
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
