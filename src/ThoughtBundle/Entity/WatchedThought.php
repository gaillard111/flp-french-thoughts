<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 17.07.19
 * Time: 14:26
 */

namespace ThoughtBundle\Entity;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\ORM\Mapping as ORM;

/**
 * Class WatchedThought
 *
 * @package ThoughtBundle\Entity
 *
 * @ORM\Entity()
 * @ORM\Table(name="watched_thoughts")
 */
class WatchedThought
{
    /**
     * @var int
     *
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;

    /**
     * @var Thought
     *
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Thought", inversedBy="watchedThoughts")
     * @ORM\JoinColumn(name="thought_id", referencedColumnName="id", onDelete="cascade")
     */
    private $thought;

    /**
     * @var User
     *
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="watchedThoughts")
     */
    private $user;

    /**
     * @return int
     */
    public function getId()
    {
        return $this->id;
    }

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
     * @return WatchedThought
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
     * @return WatchedThought
     */
    public function setUser($user)
    {
        $this->user = $user;
        return $this;
    }
}