<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Thought;

class LikeRepository extends EntityRepository
{
    /**
     * @param User $user
     * @param Thought $thought
     * @return bool
     * @throws \Doctrine\ORM\NonUniqueResultException
     */
    public function isUserLikeThought(User $user, Thought $thought): bool
    {
        $qb = $this->createQueryBuilder('l');
        $qb
            ->where('l.user = :user')
            ->andWhere('l.thought = :thought')
            ->setParameters(['user' => $user, 'thought' => $thought]);

        return !is_null($qb->getQuery()->getOneOrNullResult());
    }
}