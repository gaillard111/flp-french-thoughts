<?php

namespace ThoughtBundle\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * Class Chain
 *
 * @ORM\Entity(repositoryClass="ThoughtBundle\Repository\ChainRepository")
 * @ORM\Table(name="chain")
 * @ORM\HasLifecycleCallbacks()
 */
class Chain
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @ORM\Column(name="name", type="string")
     */
    protected $name;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="chains")
     * @ORM\JoinColumn(name="user_id", referencedColumnName="id")
     */
    protected $user;

    /**
     * @ORM\Column(name="is_private", type="boolean")
     */
    protected $isPrivate = true;

    /**
     * @ORM\Column(name="is_collective", type="boolean")
     */
    protected $isCollective = false;

    /**
     * @ORM\Column(name="created_at", type="datetime")
     */
    protected $createdAt;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ChainComment", mappedBy="chain", cascade={"remove"})
     */
    protected $comments;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ThoughtChain", mappedBy="chain", cascade={"remove"})
     */
    protected $chainThoughts;

    /**
     * @ORM\Column(name="favorite", type="boolean")
     */
    protected $favorite = false;

    /**
     * @return mixed
     */
    public function getisCollective()
    {
        return $this->isCollective;
    }

    /**
     * @param mixed $isCollective
     */
    public function setIsCollective($isCollective)
    {
        $this->isCollective = $isCollective;
    }

    /**
     * @return mixed
     */
    public function getFavorite()
    {
        return $this->favorite;
    }

    /**
     * @param mixed $favorite
     */
    public function setFavorite($favorite)
    {
        $this->favorite = $favorite;
    }

    /**
     * @ORM\PrePersist
     */
    public function setCreatedAtValue()
    {
        $this->createdAt = new \DateTime();
    }
    /**
     * Constructor
     */
    public function __construct()
    {
        $this->comments = new \Doctrine\Common\Collections\ArrayCollection();
        $this->chainThoughts = new \Doctrine\Common\Collections\ArrayCollection();
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
     * Set name
     *
     * @param string $name
     * @return Chain
     */
    public function setName($name)
    {
        $this->name = $name;

        return $this;
    }

    /**
     * Get name
     *
     * @return string 
     */
    public function getName()
    {
        return $this->name;
    }

    /**
     * Set isPrivate
     *
     * @param boolean $isPrivate
     * @return Chain
     */
    public function setIsPrivate($isPrivate)
    {
        $this->isPrivate = $isPrivate;

        return $this;
    }

    /**
     * Get isPrivate
     *
     * @return boolean 
     */
    public function getIsPrivate()
    {
        return $this->isPrivate;
    }

    /**
     * Set createdAt
     *
     * @param \DateTime $createdAt
     * @return Chain
     */
    public function setCreatedAt($createdAt)
    {
        $this->createdAt = $createdAt;

        return $this;
    }

    /**
     * Get createdAt
     *
     * @return \DateTime 
     */
    public function getCreatedAt()
    {
        return $this->createdAt;
    }

    /**
     * Set user
     *
     * @param \Application\Sonata\UserBundle\Entity\User $user
     * @return Chain
     */
    public function setUser(\Application\Sonata\UserBundle\Entity\User $user = null)
    {
        $this->user = $user;

        return $this;
    }

    /**
     * Get user
     *
     * @return \Application\Sonata\UserBundle\Entity\User 
     */
    public function getUser()
    {
        return $this->user;
    }

    /**
     * Add comments
     *
     * @param \ThoughtBundle\Entity\ChainComment $comments
     * @return Chain
     */
    public function addComment(\ThoughtBundle\Entity\ChainComment $comments)
    {
        $this->comments[] = $comments;

        return $this;
    }

    /**
     * Remove comments
     *
     * @param \ThoughtBundle\Entity\ChainComment $comments
     */
    public function removeComment(\ThoughtBundle\Entity\ChainComment $comments)
    {
        $this->comments->removeElement($comments);
    }

    /**
     * Get comments
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getComments()
    {
        return $this->comments;
    }

    /**
     * Add chainThoughts
     *
     * @param \ThoughtBundle\Entity\ThoughtChain $chainThoughts
     * @return Chain
     */
    public function addChainThought(\ThoughtBundle\Entity\ThoughtChain $chainThoughts)
    {
        $this->chainThoughts[] = $chainThoughts;

        return $this;
    }

    /**
     * Remove chainThoughts
     *
     * @param \ThoughtBundle\Entity\ThoughtChain $chainThoughts
     */
    public function removeChainThought(\ThoughtBundle\Entity\ThoughtChain $chainThoughts)
    {
        $this->chainThoughts->removeElement($chainThoughts);
    }

    /**
     * Get chainThoughts
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChainThoughts()
    {
        return $this->chainThoughts;
    }
}
