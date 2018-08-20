<?php

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\ORM\Mapping as ORM;

/**
 * Dialog
 *
 * @ORM\Table(name="dialogs")
 * @ORM\Entity(repositoryClass="Application\Sonata\UserBundle\Repository\DialogRepository")
 */
class Dialog
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
     * @ORM\ManyToMany(targetEntity="Application\Sonata\UserBundle\Entity\User", mappedBy="dialogs")
     */
    private $users;

    /**
     * @ORM\OneToMany(targetEntity="Application\Sonata\UserBundle\Entity\Message", mappedBy="dialog")
     */
    private $messages;

    /**
     * @return mixed
     */
    public function getUsers()
    {
        return $this->users;
    }

    public function __construct()
    {
        $this->messages = new ArrayCollection();
        $this->users = new ArrayCollection();
    }

    public function addMessage(Message $message)
    {
        $this->messages[] = $message;
        return $this->messages;
    }

    public function addUser(User $user)
    {
        $this->users[] = $user;
        return $this->users;
    }

    /**
     * @return mixed
     */
    public function getMessages()
    {
        return $this->messages;
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
