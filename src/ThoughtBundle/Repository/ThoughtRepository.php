<?php

namespace ThoughtBundle\Repository;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityRepository;
use ThoughtBundle\Entity\Thought;

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
}