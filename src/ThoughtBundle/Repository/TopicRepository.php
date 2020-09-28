<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 28.11.18
 * Time: 14:57
 */

namespace ThoughtBundle\Repository;

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

    public function searchTopics($role, Topic $topic = null, User $user = null)
    {
        $parameters = [];

        $qb = $this->createQueryBuilder('t');
        $qb
            ->select('t, c, ct, thought, u, topicowner')
            ->leftJoin('t.user', 'topicowner')
            ->leftJoin('t.chains', 'c')
            ->leftJoin('c.chainThoughts', 'ct')
            ->leftJoin('ct.thought', 'thought')
            ->leftJoin('thought.owner', 'u')
        ;

        if ($user) {
            $qb->andWhere('t.user = :user');
            $parameters = array_merge($parameters, [
                'user' => $user,
            ]);
        } else {
            if ($role == User::ROLE_USER) {
                $qb->andWhere('topicowner.roles NOT LIKE :roles');
//                $qb->orWhere('u.roles IS NULL');
            } else {
                $qb->andWhere('topicowner.roles LIKE :roles');
//                $qb->orWhere('u.roles IS NULL');
            }
            $parameters = array_merge($parameters, [
                'roles'    => '%' . User::ROLE_STUDENT . '%',
            ]);
        }

        $qb->orderBy('c.name', 'ASC');
        $qb->orderBy('thought.category', 'ASC');
        $qb->orderBy('t.name', 'ASC');

        if ($topic) {
            $parameters = array_merge($parameters, [
                'topicName' => '%' . $topic->getName() . '%',
            ]);

            $qb
                ->orWhere('c.name LIKE :topicName')
                ->orderBy('c.name', 'ASC')
            ;
        }

        $qb->setParameters($parameters);

        return $qb->getQuery()->getResult();
    }
}