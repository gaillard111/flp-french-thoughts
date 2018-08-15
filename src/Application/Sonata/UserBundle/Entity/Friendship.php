<?php

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Friendship
 *
 * @ORM\Table(name="friendship")
 * @ORM\Entity(repositoryClass="Application\Sonata\UserBundle\Repository\FriendshipRepository")
 */
class Friendship
{
    /**
     * @var int
     *
     * @ORM\Column(name="id", type="integer")
     * @ORM\Id
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;


    /**
     * @var int
     * @ORM\Column(name="id_user", type="integer")
     */
    private $user;

    /**
     * @var int
     * @ORM\Column(name="id_friend", type="integer")
     */
    private $friend;

    /**
     * @var boolean
     * @ORM\Column(name="accepted", type="boolean)
     */
    private $accepted = false;

    /**
     * @return bool
     */
    public function isAccepted()
    {
        return $this->accepted;
    }

    /**
     * @param bool $accepted
     */
    public function setAccepted($accepted)
    {
        $this->accepted = $accepted;
    }

    /**
     * @return int
     */
    public function getFriend()
    {
        return $this->friend;
    }

    /**
     * @param int $friend
     */
    public function setFriend($friend)
    {
        $this->friend = $friend;
    }


    /**
     * @return int
     */
    public function getUser()
    {
        return $this->user;
    }

    /**
     * @param int $user
     */
    public function setUser($user)
    {
        $this->user = $user;
    }

    /**
     * Get id
     *
     * @return integer 
     */
    public function getId()
    {
        return $this->id;
    }
}
