<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 28.11.18
 * Time: 14:57
 */

namespace Application\Sonata\UserBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Topic;

class TopicRepository extends EntityRepository
{
    public function getCountUserTopics(User $user)
    {
        $qb = $this->createQueryBuilder('t');
        $qb
            ->select('count(t.id)')
            ->where('t.user = :user')
            ->setParameter('user', $user);
        return $qb->getQuery()->getOneOrNullResult();
    }

    public function searchTopics(Topic $topic)
    {
        $qb = $this->createQueryBuilder('t');
        $qb
            ->select('t')
            ->leftJoin('t.chains', 'c')
            ->where('t.name LIKE :topicName')
            ->orWhere('c.name LIKE :topicName')
            ->setParameters([
                'topicName' => '%' . $topic->getName() . '%',
            ]);
        return $qb->getQuery()->getResult();
    }
}