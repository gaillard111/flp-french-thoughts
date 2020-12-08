<?php

namespace Application\Sonata\UserBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;

class UserRepository extends EntityRepository
{
    public function getStandardUsersQuery () {
        $qb = $this->createQueryBuilder('u');
        $qb->andWhere('u.roles not LIKE :role1 AND u.roles not LIKE :role2');
        $qb->setParameters([
            'role1' => '%'. User::ROLE_STUDENT. '%',
            'role2' => '%'. User::ROLE_TEACHER. '%'
        ]);
        return $qb->getQuery();
    }

    public function getStudentAndTeacherQuery () {
        $qb = $this->createQueryBuilder('u');
        $qb->andWhere('u.roles LIKE :role1 OR u.roles LIKE :role2');
        $qb->setParameters([
            'role1' => '%'. User::ROLE_STUDENT. '%',
            'role2' => '%'. User::ROLE_TEACHER. '%'
        ]);
        return $qb->getQuery();
    }

    public function getStudentsLike($userName) {
        return $this->createQueryBuilder('u')
            ->where('u.firstname LIKE :name OR u.lastname LIKE :name')
            ->andWhere('u.roles LIKE :roles')
            ->setParameters([
                'name' => '%' . $userName . '%',
                'roles' => '%' . User::ROLE_STUDENT . '%',
            ])
            ->getQuery()
            ->getResult();
    }

    public function getAllStudentsQuery() {
        $qb = $this->createQueryBuilder('u');
        $qb->andWhere('u.roles LIKE :role');
        $qb->setParameters([
            'role' => '%'. User::ROLE_STUDENT. '%',
        ]);
        return $qb->getQuery();
    }

    public function getAllTeachersQuery() {
        $qb = $this->createQueryBuilder('u');
        $qb->andWhere('u.roles LIKE :role');
        $qb->setParameters([
            'role' => '%'. User::ROLE_TEACHER. '%',
        ]);
        return $qb->getQuery();
    }
}