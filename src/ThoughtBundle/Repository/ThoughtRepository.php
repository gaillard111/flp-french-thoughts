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
}