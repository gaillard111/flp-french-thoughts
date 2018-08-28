<?php

namespace ThoughtBundle\Repository;

use Doctrine\ORM\EntityRepository;

class ThoughtRepository extends EntityRepository
{

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