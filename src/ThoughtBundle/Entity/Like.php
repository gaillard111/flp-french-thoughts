<?php

namespace ThoughtBundle\Entity;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\Mapping as ORM;

/**
 * Class Like
 *
 * @package ThoughtBundle\Entity
 *
 * @ORM\Entity()
 * @ORM\Table(name="likes")
 */
class Like
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @var Thought
     *
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Thought", inversedBy="likes")
     * @ORM\JoinColumn(name="thought_id", referencedColumnName="id", onDelete="cascade")
     */
    private $thought;

    /**
     * @var User
     *
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="likes")
     * @ORM\JoinColumn(name="user_id", referencedColumnName="id", nullable=true)
     */
    private $user;

    /**
     * @return Thought
     */
    public function getThought()
    {
        return $this->thought;
    }

    /**
     * @param Thought $thought
     *
     * @return Like
     */
    public function setThought($thought)
    {
        $this->thought = $thought;
        return $this;
    }

    /**
     * @return User
     */
    public function getUser()
    {
        return $this->user;
    }

    /**
     * @param User $user
     *
     * @return Like
     */
    public function setUser($user)
    {
        $this->user = $user;
        return $this;
    }
}