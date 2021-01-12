<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use Doctrine\ORM\Query;

class ThoughtRepository extends EntityRepository
{
    /**
     * @param User $user
     *
     * @return array
     */
    public function getLikedThoughts(User $user)
    {
        $qb = $this->createQueryBuilder('t');
        $qb
            ->join('t.likes', 'l')
            ->where('l.user = :user')
            ->setParameter('user', $user);

        return $qb->getQuery();
    }

    /**
     * @param array $where
     * @param null  $sortOrder
     * @param null  $sortBy
     *
     * @return array
     */
    public function getFilterThoughts(array $where = [], $sortOrder = null, $sortBy = null)
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
     * @param $sortField
     * @param $sortDirection
     * @param $role
     *
     * @return Query
     */
    public function getLastThoughts($limit, $sortField, $sortDirection, $role)
    {
        $qb = $this->createQueryBuilder('t')
            ->select('t')
            ->leftJoin('t.owner', 'u')
            ->where('t.published = true')
            ->setMaxResults($limit);
        ;

        if ($role !== User::ROLE_STUDENT and $role !== User::ROLE_TEACHER){
            $qb->andWhere('u.roles NOT IN (:role1, :role2) OR t.owner is null');
            $qb->setParameters([
                'role1' => serialize([User::ROLE_STUDENT]),
                'role2' => serialize([User::ROLE_TEACHER])
            ]);
        }

        if ($sortField == 'likesCount') {
            $qb
                ->select('t, count(l.id) as HIDDEN likesCount')
                ->leftJoin('t.likes', 'l')
                ->groupBy('t.id')
                ->orderBy($sortField, $sortDirection)
            ;
            return $qb->getQuery();
        }

        $qb->orderBy('t.' . $sortField, $sortDirection);

        return $qb->getQuery();
    }

    /**
     * @param User  $user
     * @param array $tags
     *
     * @return array
     */
    public function getUnseenUserThoughts(User $user, array $tags)
    {
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

        $tagNumber        = 0;
        $parameters       = [];
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

        return $qb->getQuery()->getResult();
    }

    /**
     * @param User $user
     *
     * @return array
     */
    public function getWatchedStatistics(User $user)
    {
        $qb = $this->createQueryBuilder('t');

        $qb
            ->select('t.tags')
            ->innerJoin('t.watchedThoughts', 'wt', 'WITH', 'wt.user = :user')
            ->setParameter('user', $user)
        ;

        return $qb->getQuery()->getResult();
    }
}
