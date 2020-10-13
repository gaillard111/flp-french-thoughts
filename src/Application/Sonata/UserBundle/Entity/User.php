<?php

/**
 * This file is part of the <name> project.
 *
 * (c) <yourname> <youremail>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Application\Sonata\UserBundle\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;
use Sonata\UserBundle\Entity\BaseUser;
use Symfony\Component\Validator\Constraints as Assert;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\ChainComment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\TeacherGroup;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\ThoughtRelated;
use ThoughtBundle\Entity\WatchedThought;

/**
 * @ORM\Entity(repositoryClass="Application\Sonata\UserBundle\Repository\UserRepository")
 * @ORM\HasLifecycleCallbacks()
 * @ORM\Table(name="fos_user_user")
 */
class User extends BaseUser
{
    const ROLE_STUDENT = 'ROLE_STUDENT';
    const ROLE_USER = 'ROLE_USER';
    const ROLE_TEACHER = 'ROLE_TEACHER';

    /**
     * @ORM\Id
     * @ORM\GeneratedValue
     * @ORM\Column(type="integer")
     */
    protected $id;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Thought", mappedBy="owner", orphanRemoval=true)
     */
    protected $thoughts;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Chain", mappedBy="user", orphanRemoval=true)
     */
    protected $chains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ChainComment", mappedBy="user", orphanRemoval=true)
     */
    protected $chainComments;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ThoughtChain", mappedBy="user")
     */
    protected $collectiveThoughtChains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Topic", mappedBy="user", orphanRemoval=true)
     */
    protected $topics;

    /**
     * @ORM\Column(name="about_me", type="string", nullable=true)
     */
    protected $about;

    /**
     * @ORM\Column(name="country", type="string", nullable=true)
     */
    protected $country;

    /**
     * @ORM\Column(name="interests", type="text", nullable=true, length=250)
     */
    protected $interests;

    /**
     * @Assert\NotBlank(groups={"CustomProfile", "CustomRegistration"})
     */
    protected $firstname;

    /**
     * @Assert\NotBlank(groups={"CustomProfile", "CustomRegistration"})
     */
    protected $lastname;

    protected $gender;


    protected $locked = false;

    /**
     * @ORM\OneToMany(targetEntity="Application\Sonata\UserBundle\Entity\Friendship", mappedBy="user", orphanRemoval=true)
     */
    protected $friendship;

    /**
     * @ORM\OneToMany(targetEntity="Application\Sonata\UserBundle\Entity\Friendship", mappedBy="friend")
     */
    protected $friends;

    /**
     * @ORM\ManyToMany(targetEntity="Application\Sonata\UserBundle\Entity\Dialog", mappedBy="users")
     */
    protected $dialogs;

    /**
     * @var ArrayCollection|Like[]
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Like", mappedBy="user", orphanRemoval=true)
     */
    protected $likes;

    /**
     * @var ArrayCollection|WatchedThought[]
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\WatchedThought", mappedBy="user", orphanRemoval=true)
     */
    protected $watchedThoughts;

    /**
     * @var ArrayCollection|Thought[]
     *
     * @ORM\ManyToMany(targetEntity="ThoughtBundle\Entity\Thought")
     * @ORM\JoinTable(name="favorite_thoughts",
     *     joinColumns={@ORM\JoinColumn(name="user_id", referencedColumnName="id")},
     *     inverseJoinColumns={@ORM\JoinColumn(name="thought_id", referencedColumnName="id")}
     *     )
     */
    protected $mostFavoriteThoughts;

    /**
     * @var ArrayCollection|ThoughtRelated[]
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ThoughtRelated", mappedBy="owner")
     */
    protected $relatedThought;

    /**
     * @ORM\ManyToMany(
     *     targetEntity="ThoughtBundle\Entity\TeacherGroup",
     *     mappedBy="students",
     *     cascade={"persist"}
     * )
     */
    protected $teacherGroup;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\TeacherGroup", mappedBy="owner", orphanRemoval=true)
     */
    protected $studentsGroup;

    public function __construct()
    {
        $this->dialogs = new ArrayCollection();
        $this->teacherGroup = new ArrayCollection();
        $this->studentsGroup = new ArrayCollection();
        parent::__construct();
    }

    /**
     * @return ArrayCollection
     */
    public function getStudentsGroup()
    {
        return $this->studentsGroup;
    }

    /**
     * @param ArrayCollection $studentsGroup
     */
    public function setStudentsGroup(ArrayCollection $studentsGroup): void
    {
        $this->studentsGroup = $studentsGroup;
    }

    /**
     * @return ArrayCollection
     */
    public function getTeacherGroup()
    {
        return $this->teacherGroup;
    }

    /**
     * @param ArrayCollection $teacherGroup
     * @return User
     */
    public function setTeacherGroup(ArrayCollection $teacherGroup): self
    {
        $this->teacherGroup = $teacherGroup;
        return $this;
    }

    /**
     * @param User $user
     * @return bool
     */
    public function isInTheTeacherGroup(User $user) {
        foreach ($this->getStudentsGroup() as $group)
        {
            if ($group->getStudents()->contains($user)){
                return true;
            }
        }

        return false;
    }

    /**
     * @return ArrayCollection
     */
    public function getDialogs()
    {
        return $this->dialogs;
    }

    /**
     * @param ArrayCollection $dialogs
     */
    public function setDialogs($dialogs)
    {
        $this->dialogs = $dialogs;
    }

    /**
     * @param Dialog $dialog
     * @return User
     */
    public function addDialog($dialog)
    {
        $dialog->addUser($this);
        $this->dialogs[] = $dialog;

        return $this;
    }


    public function getRoles()
    {
        $roles = $this->roles;

        if (count($roles) == 0) {
            $roles[] = static::ROLE_DEFAULT;
            return array_unique($roles);
        }

        foreach ($this->getGroups() as $group) {
            $roles = array_merge($roles, $group->getRoles());
        }

        return array_unique($roles);
    }

    /**
     * @return int $id
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @param Thought $thoughts
     * @return User
     */
    public function addThought(Thought $thoughts)
    {
        $this->thoughts[] = $thoughts;

        return $this;
    }

    /**
     * @param Thought $thoughts
     */
    public function removeThought(Thought $thoughts)
    {
        $this->thoughts->removeElement($thoughts);
    }

    /**
     * @return Collection
     */
    public function getThoughts()
    {
        return $this->thoughts;
    }

    /**
     * @inheritdoc
     */
    public function prePersist(): void
    {
        parent::prePersist();
        $this->username = $this->email;
    }

    /**
     * @inheritdoc
     */
    public function preUpdate(): void
    {
        parent::preUpdate();
        $this->username = $this->email;
    }

    /**
     * @param Chain $chains
     * @return User
     */
    public function addChain(Chain $chains)
    {
        $this->chains[] = $chains;

        return $this;
    }

    /**
     * @param Chain $chains
     */
    public function removeChain(Chain $chains)
    {
        $this->chains->removeElement($chains);
    }

    /**
     * @return Collection
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * @param ChainComment $chainComments
     * @return User
     */
    public function addChainComment(ChainComment $chainComments)
    {
        $this->chainComments[] = $chainComments;

        return $this;
    }

    public function getTopics()
    {
        return $this->topics;
    }

    /**
     * @return User
     */
    public function setTopics($topics)
    {
        $this->topics = $topics;
        return $this;
    }

    /**
     * @param ChainComment $chainComments
     */
    public function removeChainComment(ChainComment $chainComments)
    {
        $this->chainComments->removeElement($chainComments);
    }

    /**
     * @return Collection
     */
    public function getChainComments()
    {
        return $this->chainComments;
    }

    /**
     * Get fullName + email
     * @return string
     */
    public function getFullNameEmail()
    {
        $fullName = trim(parent::getFullname());

        return  (!empty($fullName) ? $fullName . ', ' : '') . $this->getEmail();
    }

    /**
     * @param string $about
     * @return User
     */
    public function setAbout($about)
    {
        $this->about = $about;

        return $this;
    }

    /**
     * @return string
     */
    public function getAbout()
    {
        return $this->about;
    }

    /**
     * @param string $country
     * @return User
     */
    public function setCountry($country)
    {
        $this->country = $country;

        return $this;
    }

    /**
     * @return string
     */
    public function getCountry()
    {
        return $this->country;
    }

    /**
     * @param string $interests
     * @return User
     */
    public function setInterests($interests)
    {
        $this->interests = $interests;

        return $this;
    }

    /**
     * @return string
     */
    public function getInterests()
    {
        return $this->interests;
    }

    /**
     * @param Friendship $friendship
     * @return User
     */
    public function addFriendship(Friendship $friendship)
    {
        $this->friendship[] = $friendship;

        return $this;
    }

    /**
     * @param Friendship $friendship
     */
    public function removeFriendship(Friendship $friendship)
    {
        $this->friendship->removeElement($friendship);
    }

    /**
     * @return Collection
     */
    public function getFriendship()
    {
        return $this->friendship;
    }

    /**
     * @param Friendship $friends
     * @return User
     */
    public function addFriend(Friendship $friends)
    {
        $this->friends[] = $friends;

        return $this;
    }

    /**
     * @param Friendship $friends
     */
    public function removeFriend(Friendship $friends)
    {
        $this->friends->removeElement($friends);
    }

    /**
     * @return Collection
     */
    public function getFriends()
    {
        return $this->friends;
    }

    /**
     * @return ArrayCollection|Thought[]
     */
    public function getMostFavoriteThoughts()
    {
        return $this->mostFavoriteThoughts;
    }

    public function addThoughtToMostFavorite(Thought $thought)
    {
        $this->mostFavoriteThoughts->add($thought);
    }

    public function deleteThoughtFromMostFavorites(Thought $thought)
    {
        $this->mostFavoriteThoughts->removeElement($thought);
    }

    public function getRole() {
        if (in_array('ROLE_STUDENT', $this->getRoles())) {
            return $this::ROLE_STUDENT;
        } elseif (in_array('ROLE_TEACHER', $this->getRoles())) {
            return $this::ROLE_TEACHER;
        } else {
            return $this::ROLE_USER;
        }
    }
}
