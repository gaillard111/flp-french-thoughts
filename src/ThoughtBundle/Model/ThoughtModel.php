<?php

namespace ThoughtBundle\Model;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\EntityManager;
use FOS\ElasticaBundle\Finder\TransformedFinder;
use ThoughtBundle\Entity\Thought;

/**
 * Class ThoughtModel
 * @package ThoughtBundle\Model
 */
class ThoughtModel
{
    /**
     * @var EntityManager
     */
    protected $em;

    /**
     * @var \Doctrine\ORM\EntityRepository
     */
    protected $repository;

    /**
     * ServiceMedia constructor.
     * @param EntityManager $em
     */
    public function __construct(EntityManager $em)
    {
        $this->em = $em;
        $this->repository = $em->getRepository('ThoughtBundle:Thought');
    }

    /**
     * @return \Doctrine\ORM\Query
     */
    public function getThoughts()
    {
        return $this->repository->createQueryBuilder('t')
            ->where('t.published = 1')
            ->orderBy('t.createdAt', 'DESC')
            ->getQuery();
    }

    /**
     * @param User $user
     * @return \Doctrine\ORM\Query
     */
    public function getUserThoughts(User $user)
    {
        return $this->repository->createQueryBuilder('t')
            ->where('t.owner = :user')
            ->orderBy('t.createdAt', 'DESC')
            ->setParameter('user', $user)
            ->getQuery();
    }


    /**
     * @param array             $request
     * @param TransformedFinder $finder
     * @param integer           $page
     * @param integer           $countItem
     * @return \Doctrine\ORM\Query|\FOS\ElasticaBundle\Paginator\PaginatorAdapterInterface|\FOS\ElasticaBundle\Paginator\TransformedPaginatorAdapter
     */
    public function getThoughtsFromElastic($request, TransformedFinder $finder, $page, $countItem)
    {
        $fields = array(
            'tags',
            'author',
            'content',
            'category',
            'thoughtInfo',
        );

        if (isset($request['field']) and  count($request['field']) > 0) {
            $fields = array_keys($request['field']);
        }

        $sort = array();

        if (isset($request['sorting']) && $request['sorting']) {
            $sort = array(
                $request['sorting'] => (isset($request['sorting_desc']) ? 'desc' : 'asc'),
            );
        }

        $maxWords = (isset($request['max_words']) && $request['max_words'] > 0) ? intval($request['max_words']) : 99999999;

        $minWords = isset($request['min_words']) ? intval($request['min_words']) : 0;

        $words = (isset($request['words']) && mb_strlen($request['words']) > 0) ? trim($request['words']) : null;

        $page = $page ? $page : 1;

        if ($words) {
            $query = new \Elastica\Query\MultiMatch();

            $query->setParams(
                array(
                    'query' => array(
                        'multi_match' => array(
                            'query' => $words,
                            'fields' => $fields,
                        ),
                    ),
                    'filter' => array(
                        'range' => array(
                            'amount' => array(
                                'gte' => $minWords,
                                'lte' => $maxWords,
                            ),
                        ),
                    ),
                    'sort' => $sort,
                )
            );

            $query->setParam('from', (($page - 1) * $countItem));
            $query->setParam('size', $countItem);
        } else {
            $query = new \Elastica\Query();

            $query->setParams(array(
                'filter' => array(
                    'range' => array(
                        'amount' => array(
                            'gte' => $minWords,
                            'lte' => $maxWords,
                        ),
                    ),
                ),
                'sort' => $sort,
            ));
        }

        $thoughts = $finder->createPaginatorAdapter($query);

        return $thoughts;
    }

    /**
     * @param array $data
     * @return int
     */
    public function saveThoughts(array $data)
    {
        $flag = false;

        $countAdded = 0;

        foreach ($data as $item) {
            if ($this->createTransaction($item)) {
                $flag = true;
                $countAdded++;
            }
        }

        if ($flag == true) {
            $this->em->flush();
        }

        return $countAdded;
    }

    /**
     * @param Thought $thought
     * @return Thought
     */
    public function addLike(Thought  $thought)
    {
        $thought->setLiked($thought->getLiked() + 1);

        $this->em->persist($thought);
        $this->em->flush();

        return $thought;
    }

    /**
     * @param Thought $thought
     * @return Thought
     */
    public function removeLike(Thought  $thought)
    {
        $thought->setLiked($thought->getLiked() - 1);

        $this->em->persist($thought);
        $this->em->flush();

        return $thought;
    }

    /**
     * @param array $data
     * @return bool|int
     */
    private function createTransaction(array $data)
    {
        $tags = (isset($data['tags'])) ? $data['tags'] : null;
        $author = (isset($data['author'])) ? $data['author'] : null;
        $content = (isset($data['content'])) ? $data['content'] : null;
        $category = (isset($data['category'])) ? $data['category'] : null;
        $published = (isset($data['published'])) ? $data['published'] : null;
        $thoughtInfo = (isset($data['info'])) ? $data['info'] : null;

        if (!empty($content)) {
            $thought = new Thought();
            $thought->setTags($tags);
            $thought->setAuthor($author);
            $thought->setContent($content);
            $thought->setCategory($category);
            $thought->setPublished($published);
            $thought->setThoughtInfo($thoughtInfo);

            $this->em->persist($thought);

            return true;
        }

        return false;
    }



}
