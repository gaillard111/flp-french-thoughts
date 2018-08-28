<?php

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

/**
 * Message
 *
 * @ORM\Table(name="messages")
 * @ORM\Entity(repositoryClass="Application\Sonata\UserBundle\Repository\MessageRepository")
 * @ORM\HasLifecycleCallbacks()
 */
class Message
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
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\Dialog", inversedBy="messages")
     * @ORM\JoinColumn(name="dialog_id")
     */
    private $dialog;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User")
     * @ORM\JoinColumn(name="sender_id")
     */
    private $sender;

    /**
     * @var string
     * @ORM\Column(name="message_text", type="text")
     * @Assert\NotBlank()
     */
    private $messageText;

    /**
     * @ORM\Column(name="created_at", type="datetime")
     */
    private $createdAt;

    /**
     * @ORM\Column(name="is_viewed", type="boolean", nullable=true)
     */
    private $isViewed = false;

    /**
     * @return mixed
     */
    public function getisViewed()
    {
        return $this->isViewed;
    }

    /**
     * @param mixed $isViewed
     * @return Message
     */
    public function setIsViewed($isViewed)
    {
        $this->isViewed = $isViewed;
        return $this;
    }

    /**
     * @return mixed
     */
    public function getCreatedAt()
    {
        return $this->createdAt;
    }

    /**
     * @ORM\PrePersist
     */
    public function setCreatedAtValue()
    {
        $this->createdAt = new \DateTime();
    }

    /**
     * @return mixed
     */
    public function getSender()
    {
        return $this->sender;
    }

    /**
     * @param mixed $sender
     */
    public function setSender($sender)
    {
        $this->sender = $sender;
    }

    /**
     * Set messageText
     *
     * @param string $messageText
     * @return Message
     */
    public function setMessageText($messageText)
    {
        $this->messageText = $messageText;

        return $this;
    }

    /**
     * Get messageText
     *
     * @return string 
     */
    public function getMessageText()
    {
        return $this->messageText;
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

    /**
     * Set dialog
     *
     * @param \Application\Sonata\UserBundle\Entity\Dialog $dialog
     * @return Message
     */
    public function setDialog(\Application\Sonata\UserBundle\Entity\Dialog $dialog = null)
    {
        $this->dialog = $dialog;

        return $this;
    }

    /**
     * Get dialog
     *
     * @return \Application\Sonata\UserBundle\Entity\Dialog 
     */
    public function getDialog()
    {
        return $this->dialog;
    }
}
