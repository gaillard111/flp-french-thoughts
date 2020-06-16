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

    public function searchTopics($role, Topic $topic = null, User $user = null)
    {
        $parameters = [];

        $notLikeRole = User::ROLE_STUDENT;

        if ($role == User::ROLE_STUDENT) {
            $notLikeRole = User::ROLE_USER;
        }

        $qb = $this->createQueryBuilder('t');
        $qb
            ->select('t, c, ct, thought, u')
            ->leftJoin('t.chains', 'c')
            ->leftJoin('c.chainThoughts', 'ct')
            ->leftJoin('ct.thought', 'thought')
            ->leftJoin('thought.owner', 'u')
        ;

        if ($role == User::ROLE_USER) {
//            dump($notLikeRole);die;
            $qb->andWhere('u.roles NOT LIKE :roles');
            $parameters = array_merge($parameters, [
                'roles' => '%' . $notLikeRole . '%',
            ]);
        }

        if ($user) {
            $qb->andWhere('t.user = :user');
            $parameters = array_merge($parameters, [
                'user' => $user,
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
//        dump($qb->getQuery()->getResult(2));die;
        return $qb->getQuery()->getResult();
    }
}