<?php

namespace Application\Sonata\UserBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;

class UserRepository extends EntityRepository
{
    public function getUsersList($role)
    {
        $parameters = [];

        $qb = $this->createQueryBuilder('u');

        if ($role == User::ROLE_USER) {
            $qb->andWhere('u.roles NOT LIKE :roles');
        } else {
            $qb->andWhere('u.roles LIKE :roles');
        }

        $parameters = array_merge($parameters, [
            'roles' => '%' . User::ROLE_STUDENT . '%',
        ]);
        $qb->setParameters($parameters);
//        dump($qb->getQuery());die;
        return $qb->getQuery();
    }
}