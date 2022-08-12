<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use DateTime;
use Doctrine\ORM\EntityRepository;

class PersonalDataRequestRepository extends EntityRepository
{
    public function getNewRequests(User $user)
    {
        $yesterday = (new DateTime('now'))->modify('-1 day');

        $qb = $this->createQueryBuilder('r')
            ->where('r.user = :user')
            ->andWhere('r.createdAt >= :yesterday')
            ->setParameters([
                'user' => $user,
                'yesterday' => $yesterday
            ]);

        return $qb->getQuery()->getOneOrNullResult();
    }

    public function deleteOutDateRequests()
    {
        $yesterday = (new DateTime('now'))->modify('-1 day');

        $qb = $this->createQueryBuilder('r')
            ->andWhere('r.createdAt < :yesterday')
            ->setParameter('yesterday', $yesterday)
            ->delete()
            ->getQuery()
            ->execute()
        ;
    }
}