<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\WatchedThought;

class ThoughtRepository extends EntityRepository
{
    public function getLikedThoughts(User $user)
    {
        $qb = $this->createQueryBuilder('t');
        $qb
            ->join('t.likes', 'l')
            ->where('l.user = :user')
            ->setParameter('user', $user);

        return $qb->getQuery()->getResult();
    }

    /**
     * @param array $where
     * @param null $sortOrder
     * @param null $sortBy
     * @return array
     */
    public function getFilterThoughts(array $where = array(), $sortOrder = null, $sortBy = null)
    {
        $query = $this->createQueryBuilder('t')
            ->where('t.id > 0');

        if ($sortBy) {
            $query->orderBy('t.' . $sortBy, $sortOrder);
        }

        if (count($where)) {
            foreach ($where as $field => $value) {
                $query->andWhere('t.' . $field . $value);
            }
        }

        return $query->getQuery()->getResult();
    }

    /**
     * @param $limit
     * @return \Doctrine\ORM\Query
     */
    public function getLastThoughts($limit)
    {
        $qb = $this->createQueryBuilder('t');
        $qb
            ->select('t')
            ->where('t.published = :published')
            ->setParameter('published', true)
            ->setMaxResults($limit)
            ->orderBy('t.createdAt', 'DESC');

        return $qb->getQuery();
    }

    public function getUnseenUserThoughts($user, $tags)
    {
        dump($user, $tags); die;
        $qb = $this->createQueryBuilder('t');

        $qb
            ->select('t, COUNT(l) as likesCount')
            ->leftJoin('t.watchedThoughts', 'wt')
            ->leftJoin('t.likes', 'l')
            ->andWhere($qb->expr()->orX('wt is null', 'wt.user != :user'))
            ->groupBy('t.id')
            ->orderBy('likesCount', 'DESC')
            ->setMaxResults(1)
        ;


//        $thoughts = $qb
//            ->select('t, COUNT(l) as likesCount')
//            ->leftJoin('t.watchedThoughts', 'wt')
//            ->leftJoin('t.likes', 'l')
//            ->getQuery()
//            ->getResult();
//
//        $qb
//            ->select('t')
//            ->where($qb->expr()->notIn('t.watchedThoughts', $thoughts));


        $tagNumber = 0;
        $parameters = [];
        $tagsOrXStatement = $qb->expr()->orX();
        foreach ($tags as $tag => $count) {
            if ($tagNumber >= 5) {
                break;
            }
            $tagNumber++;
            $tagsOrXStatement->add('t.tags LIKE :tag' . $tagNumber);
            $parameters['tag' . $tagNumber] = '%' . $tag . '%';
        }

        $qb->andWhere($tagsOrXStatement);

        $qb->setParameters(array_merge($parameters, ['user' => $user]));

//        $qb->orderBy('l');


//        dump($qb->getQuery()->getResult()); die;

        return $qb->getQuery()->getResult();
    }

    public function getWatchedStatistics(User $user)
    {
        $qb = $this->createQueryBuilder('t');

        $qb
            ->select('t.tags')
            ->innerJoin('t.watchedThoughts', 'wt', 'WITH', 'wt.user = :user')
            ->setParameter('user', $user)
        ;

        return $qb->getQuery()->getResult();

//        dump($qb->getQuery()->getResult());die;
    }
}