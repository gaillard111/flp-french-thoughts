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
use Sonata\UserBundle\Entity\BaseUser as BaseUser;
use Symfony\Component\Validator\Constraints as Assert;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\ChainComment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\WatchedThought;

/**
 * @ORM\Entity(repositoryClass="Application\Sonata\UserBundle\Repository\UserRepository")
 * @ORM\HasLifecycleCallbacks()
 */
class User extends BaseUser
{
    const ROLE_STUDENT = 'ROLE_STUDENT';
    const ROLE_USER = 'ROLE_USER';

    /**
     * @var int $id
     */
    protected $id;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Thought", mappedBy="owner")
     */
    protected $thoughts;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Chain", mappedBy="user")
     */
    protected $chains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ChainComment", mappedBy="user")
     */
    protected $chainComments;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ThoughtChain", mappedBy="user")
     */
    protected $collectiveThoughtChains;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Topic", mappedBy="user")
     */
    protected $topics;

    protected $about;

    protected $country;

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

    /**
     * @ORM\OneToMany(targetEntity="Application\Sonata\UserBundle\Entity\Friendship", mappedBy="user")
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
     *
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Like", mappedBy="user")
     */
    protected $likes;

    /**
     * @var ArrayCollection|WatchedThought[]
     *
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\WatchedThought", mappedBy="user")
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
     *
     * @return User
     */
    public function addDialog($dialog)
    {
        $dialog->addUser($this);
        $this->dialogs[] = $dialog;

        return $this;
    }

    public function __construct()
    {
        $this->dialogs = new ArrayCollection();
        parent::__construct();
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
     * Get id
     *
     * @return int $id
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Add thoughts
     *
     * @param Thought $thoughts
     *
     * @return User
     */
    public function addThought(Thought $thoughts)
    {
        $this->thoughts[] = $thoughts;

        return $this;
    }

    /**
     * Remove thoughts
     *
     * @param Thought $thoughts
     */
    public function removeThought(Thought $thoughts)
    {
        $this->thoughts->removeElement($thoughts);
    }

    /**
     * Get thoughts
     *
     * @return Collection
     */
    public function getThoughts()
    {
        return $this->thoughts;
    }

    /**
     * @inheritdoc
     */
    public function prePersist()
    {
        parent::prePersist();
        $this->username = $this->email;
    }

    /**
     * @inheritdoc
     */
    public function preUpdate()
    {
        parent::preUpdate();
        $this->username = $this->email;
    }

    /**
     * Add chains
     *
     * @param Chain $chains
     *
     * @return User
     */
    public function addChain(Chain $chains)
    {
        $this->chains[] = $chains;

        return $this;
    }

    /**
     * Remove chains
     *
     * @param Chain $chains
     */
    public function removeChain(Chain $chains)
    {
        $this->chains->removeElement($chains);
    }

    /**
     * Get chains
     *
     * @return Collection
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * Add chainComments
     *
     * @param ChainComment $chainComments
     *
     * @return User
     */
    public function addChainComment(ChainComment $chainComments)
    {
        $this->chainComments[] = $chainComments;

        return $this;
    }

    /**
     * @return mixed
     */
    public function getTopics()
    {
        return $this->topics;
    }

    /**
     * @param mixed $topics
     *
     * @return User
     */
    public function setTopics($topics)
    {
        $this->topics = $topics;
        return $this;
    }

    /**
     * Remove chainComments
     *
     * @param ChainComment $chainComments
     */
    public function removeChainComment(ChainComment $chainComments)
    {
        $this->chainComments->removeElement($chainComments);
    }

    /**
     * Get chainComments
     *
     * @return Collection
     */
    public function getChainComments()
    {
        return $this->chainComments;
    }

    /**
     * Get fullName + email
     *
     * @return string
     */
    public function getFullNameEmail()
    {
        $fullName = trim(parent::getFullname());

        return  (!empty($fullName) ? $fullName . ', ' : '') . $this->getEmail();
    }

    /**
     * Set about
     *
     * @param string $about
     *
     * @return User
     */
    public function setAbout($about)
    {
        $this->about = $about;

        return $this;
    }

    /**
     * Get about
     *
     * @return string
     */
    public function getAbout()
    {
        return $this->about;
    }

    /**
     * Set country
     *
     * @param string $country
     *
     * @return User
     */
    public function setCountry($country)
    {
        $this->country = $country;

        return $this;
    }

    /**
     * Get country
     *
     * @return string
     */
    public function getCountry()
    {
        return $this->country;
    }

    /**
     * Set interests
     *
     * @param string $interests
     *
     * @return User
     */
    public function setInterests($interests)
    {
        $this->interests = $interests;

        return $this;
    }

    /**
     * Get interests
     *
     * @return string
     */
    public function getInterests()
    {
        return $this->interests;
    }

    /**
     * Add friendship
     *
     * @param Friendship $friendship
     *
     * @return User
     */
    public function addFriendship(Friendship $friendship)
    {
        $this->friendship[] = $friendship;

        return $this;
    }

    /**
     * Remove friendship
     *
     * @param Friendship $friendship
     */
    public function removeFriendship(Friendship $friendship)
    {
        $this->friendship->removeElement($friendship);
    }

    /**
     * Get friendship
     *
     * @return Collection
     */
    public function getFriendship()
    {
        return $this->friendship;
    }

    /**
     * Add friends
     *
     * @param Friendship $friends
     *
     * @return User
     */
    public function addFriend(Friendship $friends)
    {
        $this->friends[] = $friends;

        return $this;
    }

    /**
     * Remove friends
     *
     * @param Friendship $friends
     */
    public function removeFriend(Friendship $friends)
    {
        $this->friends->removeElement($friends);
    }

    /**
     * Get friends
     *
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
}
