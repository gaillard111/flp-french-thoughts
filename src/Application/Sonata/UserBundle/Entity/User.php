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
use Doctrine\ORM\Mapping as ORM;
use Sonata\UserBundle\Entity\BaseUser as BaseUser;
use Symfony\Component\Validator\Constraints as Assert;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\WatchedThought;

/**
 * @ORM\Entity
 * @ORM\HasLifecycleCallbacks()
 */
class User extends BaseUser
{
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
     * @param \ThoughtBundle\Entity\Thought $thoughts
     *
     * @return User
     */
    public function addThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts[] = $thoughts;

        return $this;
    }

    /**
     * Remove thoughts
     *
     * @param \ThoughtBundle\Entity\Thought $thoughts
     */
    public function removeThought(\ThoughtBundle\Entity\Thought $thoughts)
    {
        $this->thoughts->removeElement($thoughts);
    }

    /**
     * Get thoughts
     *
     * @return \Doctrine\Common\Collections\Collection
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
     * @param \ThoughtBundle\Entity\Chain $chains
     *
     * @return User
     */
    public function addChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains[] = $chains;

        return $this;
    }

    /**
     * Remove chains
     *
     * @param \ThoughtBundle\Entity\Chain $chains
     */
    public function removeChain(\ThoughtBundle\Entity\Chain $chains)
    {
        $this->chains->removeElement($chains);
    }

    /**
     * Get chains
     *
     * @return \Doctrine\Common\Collections\Collection
     */
    public function getChains()
    {
        return $this->chains;
    }

    /**
     * Add chainComments
     *
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     *
     * @return User
     */
    public function addChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
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
     * @param \ThoughtBundle\Entity\ChainComment $chainComments
     */
    public function removeChainComment(\ThoughtBundle\Entity\ChainComment $chainComments)
    {
        $this->chainComments->removeElement($chainComments);
    }

    /**
     * Get chainComments
     *
     * @return \Doctrine\Common\Collections\Collection
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
     * @param \Application\Sonata\UserBundle\Entity\Friendship $friendship
     *
     * @return User
     */
    public function addFriendship(\Application\Sonata\UserBundle\Entity\Friendship $friendship)
    {
        $this->friendship[] = $friendship;

        return $this;
    }

    /**
     * Remove friendship
     *
     * @param \Application\Sonata\UserBundle\Entity\Friendship $friendship
     */
    public function removeFriendship(\Application\Sonata\UserBundle\Entity\Friendship $friendship)
    {
        $this->friendship->removeElement($friendship);
    }

    /**
     * Get friendship
     *
     * @return \Doctrine\Common\Collections\Collection
     */
    public function getFriendship()
    {
        return $this->friendship;
    }

    /**
     * Add friends
     *
     * @param \Application\Sonata\UserBundle\Entity\Friendship $friends
     *
     * @return User
     */
    public function addFriend(\Application\Sonata\UserBundle\Entity\Friendship $friends)
    {
        $this->friends[] = $friends;

        return $this;
    }

    /**
     * Remove friends
     *
     * @param \Application\Sonata\UserBundle\Entity\Friendship $friends
     */
    public function removeFriend(\Application\Sonata\UserBundle\Entity\Friendship $friends)
    {
        $this->friends->removeElement($friends);
    }

    /**
     * Get friends
     *
     * @return \Doctrine\Common\Collections\Collection
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
