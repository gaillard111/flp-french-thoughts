<?php

namespace ThoughtBundle\Entity;

use Application\Sonata\UserBundle\Entity\User;
use DateTime;
use Doctrine\ORM\Mapping as ORM;

/**
 * User wrapper for chat
 *
 * @ORM\Entity()
 * @ORM\Table(name="chat_participant")
 **/
class ChatParticipant
{
    /**
     * @var int
     * @ORM\Id
     * @ORM\Column(name="id", type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;

    /**
     * @ORM\ManyToOne(targetEntity="ThoughtBundle\Entity\Chat", inversedBy="participants")
     * @ORM\JoinColumn(name="chat_id", referencedColumnName="id", nullable=false)
     */
    private $chat;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="chatsParticipant")
     * @ORM\JoinColumn(name="user_id", nullable=false)
     */
    private $user;

    /**
     * @ORM\Column(name="last_visit_at", type="datetime", nullable=false)
     */
    private $lastVisitedAt;

    /**
     * ChatLastVisit constructor.
     * @param $chat
     * @param $user
     * @param $lastVisitedAt
     */
    public function __construct($chat, $user, $lastVisitedAt)
    {
        $this->chat = $chat;
        $this->user = $user;
        $this->lastVisitedAt = $lastVisitedAt;
    }

    /**
     * @return User
     */
    public function getUser()
    {
        return $this->user;
    }

    /**
     * @return Chat
     */
    public function getChat()
    {
        return $this->chat;
    }

    /**
     * @return DateTime
     */
    public function getLastVisitedAt()
    {
        return $this->lastVisitedAt;
    }

    /**
     * @param DateTime $lastVisitedAt
     * @return ChatParticipant
     */
    public function setLastVisitedAt(DateTime $lastVisitedAt): self
    {
        $this->lastVisitedAt = $lastVisitedAt;
        return $this;
    }


    /**
     * @return bool
     */
    public function isNotReadMessage(): bool
    {
        $chatMessages = $this->getChat()->getMessages();
        if (!$chatMessages->isEmpty()) {
            if ($chatMessages->last()->getCreatedAt() > $this->getLastVisitedAt()) {
                return true;
            }
        }
        return false;
    }
}