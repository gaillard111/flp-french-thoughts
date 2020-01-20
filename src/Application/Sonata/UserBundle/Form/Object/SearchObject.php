<?php

namespace Application\Sonata\UserBundle\Form\Object;

class SearchObject
{
    private $searchString;

    private $sort = 'DESC';

    /**
     * @return mixed
     */
    public function getSearchString()
    {
        return $this->searchString;
    }

    /**
     * @param mixed $searchString
     *
     * @return SearchObject
     */
    public function setSearchString($searchString)
    {
        $this->searchString = $searchString;
        return $this;
    }

    /**
     * @return string
     */
    public function getSort()
    {
        return $this->sort;
    }

    /**
     * @param string $sort
     *
     * @return SearchObject
     */
    public function setSort($sort)
    {
        $this->sort = $sort;
        return $this;
    }
}