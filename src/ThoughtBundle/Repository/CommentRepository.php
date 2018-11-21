<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 20.11.18
 * Time: 19:35
 */

namespace ThoughtBundle\Repository;

use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Thought;

class CommentRepository extends EntityRepository
{
    public function getLastComments(Thought $thought, $limit = 3)
    {
        $qb = $this->createQueryBuilder('c');
        $qb
            ->where('c.thought = :thought')
            ->setParameter('thought', $thought)
            ->orderBy('c.id', 'DESC')
            ->setMaxResults($limit);
        return $qb->getQuery()->getResult();
    }
}