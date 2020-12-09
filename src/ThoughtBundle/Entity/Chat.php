<?php


namespace ThoughtBundle\Entity;

use Application\Sonata\UserBundle\Entity\User;
use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Doctrine\ORM\Mapping\JoinColumn;
use Doctrine\ORM\Mapping\OneToOne;

/**
 * Chat
 *
 * @ORM\Entity()
 * @ORM\Table(name="chat")
 */
class Chat
{
    const PRIVATE = 'private';
    const GROUP = 'group';

    /**
     * @var int
     *
     * @ORM\Column(name="id", type="integer")
     * @ORM\Id
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    private $id;

    /**
     * @ORM\OneToMany(
     *     targetEntity="ThoughtBundle\Entity\ChatParticipant",
     *     mappedBy="chat",
     *     orphanRemoval=true,
     *     cascade={"persist"}
     * )
     */
    private $participants;

    /**
     * @ORM\OneToMany(
     *     targetEntity="ThoughtBundle\Entity\Message",
     *     mappedBy="chat",
     *     orphanRemoval=true,
     *     cascade={"persist"}
     * )
     * @ORM\OrderBy({"createdAt" = "ASC"})
     */
    private $messages;

    /**
     * @ORM\Column(name="chat_type", type="string", nullable=false)
     */
    private $chatType;

    /**
    * @OneToOne(targetEntity="ThoughtBundle\Entity\TeacherGroup", inversedBy="chat")
    * @JoinColumn(name="group_id", referencedColumnName="id")
    */
    private $group;

    public function __construct(string $chatType)
    {
        $this->chatType = $chatType;
        $this->messages      = new ArrayCollection();
        $this->participants  = new ArrayCollection();
    }

    /**
     * @return int
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @param User $user
     */
    public function addUser(User $user)
    {
        if (!$this->getUsers()->contains($user)) {
            $participant = new ChatParticipant($this, $user, new \DateTime("now"));
            $this->participants->add($participant);
        }
    }

    /**
     * @param ArrayCollection $user
     */
    public function addCollectionUsers(ArrayCollection $users) {
        foreach ($users as $user) {
            $this->addUser($user);
        }
    }

    /**
     * @return ArrayCollection
     */
    public function getUsers() {
        $users = $this->participants->map(function ($value) {
            return $value->getUser();
        });

        return $users;
    }

    /**
     * @param User $user
     * @param string $message
     */
    public function addMessage(User $user, string $message)
    {
        if (!$this->getUsers()->contains($user)) {
            throw new \LogicException('User not a member of this chat');
        }
        $objectMessage = new Message($user, $message, $this);
        $this->messages->add($objectMessage);
    }

    /**
     * @return Collection
     */
    public function getMessages(): Collection
    {
        return $this->messages;
    }

    /**
     * @return string
     */
    public function getChatType(): string
    {
        return $this->chatType;
    }

    /**
     * @param string $chatType
     * @return Chat
     */
    public function setChatType(string $chatType): self
    {
        $this->chatType = $chatType;
        return $this;
    }

    /**
     * @return TeacherGroup
     */
    public function getGroup()
    {
        return $this->group;
    }

    /**
     * @param TeacherGroup $group
     */
    public function setGroup(TeacherGroup $group): void
    {
        $this->group = $group;
    }

    public function isNotReadMessages($user) {
        if (!$this->participants->isEmpty()) {
            foreach ($this->participants as $participant) {
                if ($participant->getUser() == $user) {
                    return $participant->isNotReadMessage();
                }
            }
        }
        return null;
    }

    public function updateLastVisit($user) {
        if (!$this->participants->isEmpty()) {
            foreach ($this->participants as $participant) {
                if ($participant->getUser() == $user) {
                    $participant->setLastVisitedAt(new \DateTime("now"));
                }
            }
        }
    }
}